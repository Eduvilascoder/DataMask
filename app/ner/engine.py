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
        return self._resolve_conflicts(all_entities)

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

        También procesa una versión en title case del texto para
        detectar nombres escritos en mayúsculas completas.

        Args:
            text: Texto a analizar.
            page: Número de página.

        Returns:
            Lista de entidades detectadas por spaCy.
        """
        doc: Doc = self._nlp(text)
        entities: list[DetectedEntity] = []

        for ent in doc.ents:
            data_type = _SPACY_LABEL_MAP.get(ent.label_)
            if data_type is None:
                continue

            # Usar score de la entidad si está disponible,
            # de lo contrario usar confianza por defecto
            confidence = SPACY_DEFAULT_CONFIDENCE
            if hasattr(ent, "kb_id_") and ent.kb_id_:
                try:
                    score = float(ent.kb_id_)
                    if 0.0 <= score <= 1.0:
                        confidence = score
                except (ValueError, TypeError):
                    pass

            entity = DetectedEntity(
                text=ent.text,
                entity_type=data_type,
                start=ent.start_char,
                end=ent.end_char,
                confidence=confidence,
                page=page,
            )
            entities.append(entity)

        # Segunda pasada: detectar nombres en texto con mayúsculas
        # spaCy funciona mejor con title case, así que convertimos
        # líneas en mayúsculas a title case y re-detectamos
        lines = text.split("\n")
        for line in lines:
            stripped = line.strip()
            # Si la línea está mayormente en mayúsculas (>60% uppercase letters)
            alpha_chars = [c for c in stripped if c.isalpha()]
            if alpha_chars and sum(1 for c in alpha_chars if c.isupper()) / len(alpha_chars) > 0.6:
                # Convertir a title case y re-procesar
                title_line = stripped.title()
                doc_title: Doc = self._nlp(title_line)
                for ent in doc_title.ents:
                    data_type = _SPACY_LABEL_MAP.get(ent.label_)
                    if data_type is None:
                        continue
                    # Buscar la posición original en el texto
                    original_text = stripped[ent.start_char:ent.end_char].strip()
                    if not original_text:
                        continue
                    # Encontrar la posición en el texto completo
                    pos = text.find(stripped)
                    if pos == -1:
                        continue
                    start = pos + ent.start_char
                    end = pos + ent.end_char
                    # Usar el texto original (en mayúsculas)
                    entity = DetectedEntity(
                        text=text[start:end],
                        entity_type=data_type,
                        start=start,
                        end=end,
                        confidence=SPACY_DEFAULT_CONFIDENCE * 0.9,  # Slightly lower confidence
                        page=page,
                    )
                    entities.append(entity)

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
