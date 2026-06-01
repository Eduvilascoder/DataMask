"""Motor NER para detección de entidades sensibles.

Combina spaCy NER para nombres y direcciones con patrones regex
para formatos argentinos específicos (DNI, CUIT/CUIL, teléfonos, etc.).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import spacy
from spacy.language import Language

from app.models import DetectedEntity, SensitiveDataType, TypeConfig
from app.ner.patterns import detect_with_regex

if TYPE_CHECKING:
    from spacy.tokens import Doc

logger = logging.getLogger(__name__)

# Confianza por defecto para entidades spaCy sin score explícito
SPACY_DEFAULT_CONFIDENCE = 0.85

# Umbral mínimo de confianza para incluir una entidad
CONFIDENCE_THRESHOLD = 0.70

# Mapeo de etiquetas spaCy a tipos de datos sensibles
_SPACY_LABEL_MAP: dict[str, SensitiveDataType] = {
    "PER": SensitiveDataType.NOMBRE,
    "LOC": SensitiveDataType.DIRECCION,
}

# Mapeo de campo TypeConfig a SensitiveDataType
_TYPE_CONFIG_MAP: dict[str, SensitiveDataType] = {
    "nombre": SensitiveDataType.NOMBRE,
    "email": SensitiveDataType.EMAIL,
    "celular": SensitiveDataType.CELULAR,
    "telefono": SensitiveDataType.TELEFONO,
    "direccion": SensitiveDataType.DIRECCION,
    "tarjeta_credito": SensitiveDataType.TARJETA_CREDITO,
    "cuenta_bancaria": SensitiveDataType.CUENTA_BANCARIA,
    "dni": SensitiveDataType.DNI,
    "cuit_cuil": SensitiveDataType.CUIT_CUIL,
    "pasaporte": SensitiveDataType.PASAPORTE,
}


class NEREngine:
    """Motor de detección de entidades sensibles.

    Combina spaCy NER para nombres y direcciones con
    patrones regex para formatos argentinos específicos.
    """

    def __init__(
        self,
        model_name: str = "es_core_news_lg",
        config: TypeConfig | None = None,
    ) -> None:
        """Inicializa el motor NER cargando el modelo spaCy.

        Args:
            model_name: Nombre del modelo spaCy a cargar.
            config: Configuración de tipos activos/inactivos.
                Si es None, se usan todos los tipos activos.
        """
        self._config = config or TypeConfig()
        self._nlp = self._load_model(model_name)
        self._active_types = self._resolve_active_types()

    @property
    def config(self) -> TypeConfig:
        """Configuración actual de tipos activos."""
        return self._config

    @config.setter
    def config(self, value: TypeConfig) -> None:
        """Actualiza la configuración y recalcula tipos activos."""
        self._config = value
        self._active_types = self._resolve_active_types()

    def detect(self, text: str, page: int) -> list[DetectedEntity]:
        """Detecta entidades sensibles en el texto dado.

        Combina resultados de spaCy y regex, filtra por umbral
        de confianza y resuelve conflictos de solapamiento.

        Args:
            text: Texto extraído de una página del PDF.
            page: Número de página donde se encontró el texto.

        Returns:
            Lista de entidades detectadas, filtradas y sin conflictos.
        """
        spacy_entities = self._detect_with_spacy(text, page)
        regex_entities = detect_with_regex(text, page)

        # Combinar ambas fuentes
        all_entities = spacy_entities + regex_entities

        # Filtrar por tipos activos
        all_entities = self._filter_by_active_types(all_entities)

        # Filtrar por umbral de confianza
        all_entities = self._filter_by_confidence(all_entities)

        # Resolver conflictos de solapamiento
        resolved = self._resolve_conflicts(all_entities)

        # Limpiar entidades que contienen newlines (cortarlas)
        cleaned: list[DetectedEntity] = []
        for ent in resolved:
            if "\n" in ent.text:
                # Tomar solo la parte antes del newline
                first_line = ent.text.split("\n")[0].strip()
                if first_line:
                    cleaned.append(DetectedEntity(
                        text=first_line,
                        entity_type=ent.entity_type,
                        start=ent.start,
                        end=ent.start + len(first_line),
                        confidence=ent.confidence,
                        page=ent.page,
                    ))
            else:
                cleaned.append(ent)

        # Expandir entidades LOC para incluir "Ciudad, País" completo
        expanded: list[DetectedEntity] = []
        for ent in cleaned:
            if ent.entity_type == SensitiveDataType.DIRECCION:
                # Buscar si hay texto tipo "Ciudad, " antes de la entidad en la misma línea
                # Ejemplo: "Santiago, Chile" → expandir para cubrir "Santiago, Chile"
                # Solo buscar en la misma línea (no cruzar newlines)
                line_start = text.rfind("\n", 0, ent.start)
                line_start = line_start + 1 if line_start != -1 else 0
                prefix = text[line_start:ent.start]
                # Buscar patrón "Palabra, " al final del prefix
                import re as _re
                match = _re.search(r'([A-ZÁÉÍÓÚÑa-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑa-záéíóúñ]+)*),\s*$', prefix)
                if match:
                    new_start = ent.start - len(match.group(0))
                    expanded.append(DetectedEntity(
                        text=text[new_start:ent.end],
                        entity_type=ent.entity_type,
                        start=new_start,
                        end=ent.end,
                        confidence=ent.confidence,
                        page=ent.page,
                    ))
                else:
                    expanded.append(ent)
            else:
                expanded.append(ent)

        # Fusionar entidades adyacentes del mismo tipo
        return self._merge_adjacent_same_type(expanded, text)

    def _load_model(self, model_name: str) -> Language:
        """Carga el modelo spaCy especificado.

        Args:
            model_name: Nombre del modelo a cargar.

        Returns:
            Modelo spaCy cargado.

        Raises:
            OSError: Si el modelo no está instalado.
        """
        try:
            nlp = spacy.load(model_name)
            logger.info("Modelo spaCy '%s' cargado correctamente.", model_name)
            return nlp
        except OSError:
            logger.error(
                "No se pudo cargar el modelo spaCy '%s'. "
                "Ejecute: python -m spacy download %s",
                model_name,
                model_name,
            )
            raise

    def _resolve_active_types(self) -> set[SensitiveDataType]:
        """Calcula el conjunto de tipos activos según la configuración.

        Returns:
            Set de SensitiveDataType que están habilitados.
        """
        active: set[SensitiveDataType] = set()
        config_dict = self._config.model_dump()

        for field_name, data_type in _TYPE_CONFIG_MAP.items():
            if config_dict.get(field_name, True):
                active.add(data_type)

        return active

    def _detect_with_spacy(self, text: str, page: int) -> list[DetectedEntity]:
        """Usa spaCy para detectar PER (nombres) y LOC (direcciones).

        Estrategia multi-pasada:
        1. Procesa el texto original con spaCy
        2. Procesa una versión normalizada (sin acentos, title case)
           para detectar nombres en mayúsculas o con acentos
        3. Mapea las posiciones de vuelta al texto original

        Args:
            text: Texto a analizar.
            page: Número de página.

        Returns:
            Lista de entidades detectadas por spaCy.
        """
        import unicodedata

        entities: list[DetectedEntity] = []

        # --- Pasada 1: texto original ---
        doc: Doc = self._nlp(text)
        for ent in doc.ents:
            data_type = _SPACY_LABEL_MAP.get(ent.label_)
            if data_type is None:
                continue
            entities.append(DetectedEntity(
                text=ent.text,
                entity_type=data_type,
                start=ent.start_char,
                end=ent.end_char,
                confidence=SPACY_DEFAULT_CONFIDENCE,
                page=page,
            ))

        # --- Pasada 2: texto normalizado (sin acentos, title case) ---
        # Esto mejora la detección de nombres en MAYÚSCULAS y con acentos
        def remove_accents(s: str) -> str:
            nfkd = unicodedata.normalize("NFKD", s)
            return "".join(c for c in nfkd if not unicodedata.combining(c))

        # Procesar línea por línea para mapear posiciones correctamente
        lines = text.split("\n")
        offset = 0
        for line in lines:
            stripped = line
            if not stripped.strip():
                offset += len(line) + 1  # +1 for \n
                continue

            # Normalizar: quitar acentos y convertir a title case
            normalized = remove_accents(stripped).title()

            # Solo re-procesar si es diferente al original
            if normalized != stripped:
                doc_norm: Doc = self._nlp(normalized)
                for ent in doc_norm.ents:
                    data_type = _SPACY_LABEL_MAP.get(ent.label_)
                    if data_type is None:
                        continue

                    # Mapear posición al texto original
                    start = offset + ent.start_char
                    end = offset + ent.end_char

                    # Verificar que no excede el texto
                    if end > len(text):
                        end = len(text)
                    if start >= len(text):
                        continue

                    original_text = text[start:end]
                    if not original_text.strip():
                        continue

                    entities.append(DetectedEntity(
                        text=original_text,
                        entity_type=data_type,
                        start=start,
                        end=end,
                        confidence=SPACY_DEFAULT_CONFIDENCE * 0.9,
                        page=page,
                    ))

            offset += len(line) + 1  # +1 for \n

        return entities

        return entities

    def _filter_by_active_types(
        self, entities: list[DetectedEntity]
    ) -> list[DetectedEntity]:
        """Filtra entidades manteniendo solo las de tipos activos.

        Args:
            entities: Lista de entidades a filtrar.

        Returns:
            Lista filtrada con solo tipos activos.
        """
        return [e for e in entities if e.entity_type in self._active_types]

    def _filter_by_confidence(
        self, entities: list[DetectedEntity]
    ) -> list[DetectedEntity]:
        """Filtra entidades por umbral de confianza >= 0.70.

        Args:
            entities: Lista de entidades a filtrar.

        Returns:
            Lista filtrada con confianza suficiente.
        """
        return [e for e in entities if e.confidence >= CONFIDENCE_THRESHOLD]

    def _resolve_conflicts(
        self, entities: list[DetectedEntity]
    ) -> list[DetectedEntity]:
        """Resuelve conflictos cuando entidades se solapan.

        Cuando dos o más entidades se solapan en posición,
        se conserva la de mayor confianza.

        Args:
            entities: Lista de entidades potencialmente solapadas.

        Returns:
            Lista sin solapamientos, conservando la de mayor confianza.
        """
        if not entities:
            return []

        # Ordenar por posición de inicio, luego por confianza descendente
        sorted_entities = sorted(
            entities, key=lambda e: (e.start, -e.confidence)
        )

        resolved: list[DetectedEntity] = []

        for entity in sorted_entities:
            # Verificar si se solapa con alguna entidad ya aceptada
            overlaps = False
            for accepted in resolved:
                if self._entities_overlap(entity, accepted):
                    # Si la nueva tiene mayor confianza, reemplazar
                    if entity.confidence > accepted.confidence:
                        resolved.remove(accepted)
                        resolved.append(entity)
                    overlaps = True
                    break

            if not overlaps:
                resolved.append(entity)

        return sorted(resolved, key=lambda e: e.start)

    def _merge_adjacent_same_type(
        self, entities: list[DetectedEntity], original_text: str = ""
    ) -> list[DetectedEntity]:
        """Fusiona entidades adyacentes del mismo tipo en una sola.

        Si "Pablo" [NOMBRE] y "Bitreras" [NOMBRE] están separadas
        solo por espacios en la misma línea, se fusionan en una sola
        entidad [NOMBRE] que cubre todo el span original.

        Args:
            entities: Lista de entidades ordenadas por posición.
            original_text: Texto original para extraer el texto real.

        Returns:
            Lista con entidades adyacentes del mismo tipo fusionadas.
        """
        if not entities:
            return []

        sorted_ents = sorted(entities, key=lambda e: e.start)
        merged: list[DetectedEntity] = [sorted_ents[0]]

        for current in sorted_ents[1:]:
            last = merged[-1]

            gap = current.start - last.end
            if (
                current.entity_type == last.entity_type
                and current.page == last.page
                and 0 <= gap <= 15
            ):
                should_merge = True

                if "\n" in last.text or "\n" in current.text:
                    should_merge = False

                # Check gap for newlines using original text
                if should_merge and original_text and last.end < len(original_text):
                    gap_content = original_text[last.end:current.start]
                    if "\n" in gap_content:
                        should_merge = False

                if should_merge:
                    new_start = last.start
                    new_end = current.end
                    # Use original text to get the real merged text
                    if original_text and new_end <= len(original_text):
                        merged_text = original_text[new_start:new_end]
                    else:
                        merged_text = last.text.rstrip() + " " + current.text.lstrip()

                    merged[-1] = DetectedEntity(
                        text=merged_text,
                        entity_type=last.entity_type,
                        start=new_start,
                        end=new_end,
                        confidence=max(last.confidence, current.confidence),
                        page=last.page,
                    )
                else:
                    merged.append(current)
            else:
                merged.append(current)

        return merged

    @staticmethod
    def _entities_overlap(a: DetectedEntity, b: DetectedEntity) -> bool:
        """Determina si dos entidades se solapan en posición.

        Args:
            a: Primera entidad.
            b: Segunda entidad.

        Returns:
            True si las entidades se solapan.
        """
        return a.start < b.end and b.start < a.end
