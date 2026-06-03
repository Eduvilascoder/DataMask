"""Motor NER para detección de entidades sensibles.

Enfoque híbrido:
- Ollama (Llama 3.1 8B) para nombres y direcciones (comprensión semántica)
- Patrones regex para formatos estructurados (DNI, CUIT, email, teléfono, etc.)
- Fallback a spaCy si Ollama no está disponible
"""

from __future__ import annotations

import logging

from app.models import DetectedEntity, SensitiveDataType, TypeConfig
from app.ner.patterns import detect_with_regex
from app.ner.ollama_client import detect_with_ollama, is_ollama_available

logger = logging.getLogger(__name__)

# Umbral mínimo de confianza para incluir una entidad
CONFIDENCE_THRESHOLD = 0.70

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
    "fecha": SensitiveDataType.FECHA,
}


class NEREngine:
    """Motor de detección de entidades sensibles.

    Usa Ollama (Llama 3.1 8B) para nombres y direcciones,
    y patrones regex para formatos argentinos específicos.
    Si Ollama no está disponible, cae a spaCy como fallback.
    """

    def __init__(
        self,
        config: TypeConfig | None = None,
        model_name: str = "es_core_news_lg",
        ollama_prompt: str | None = None,
    ) -> None:
        """Inicializa el motor NER.

        Args:
            config: Configuración de tipos activos/inactivos.
            model_name: Nombre del modelo spaCy (fallback).
            ollama_prompt: Prompt personalizado para Ollama.
        """
        self._config = config or TypeConfig()
        self._active_types = self._resolve_active_types()
        self._ollama_available = is_ollama_available()
        self._ollama_prompt = ollama_prompt
        self._spacy_nlp = None  # Lazy load solo si se necesita

        if self._ollama_available:
            logger.info("Ollama disponible — usando Llama 3.1 8B para NER")
        else:
            logger.warning(
                "Ollama no disponible — usando spaCy como fallback. "
                "Para mejor detección, inicie Ollama: ollama serve"
            )
            self._load_spacy_fallback(model_name)

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
        # Detección con Ollama (nombres y direcciones) o spaCy fallback
        if self._ollama_available:
            semantic_entities = detect_with_ollama(
                text, page, prompt_template=self._ollama_prompt
            )
        else:
            semantic_entities = self._detect_with_spacy(text, page)

        # Detección con regex (formatos estructurados)
        regex_entities = detect_with_regex(text, page)

        # Heurística: detectar nombres en líneas en mayúsculas
        # (siempre se ejecuta como complemento, especialmente útil
        # cuando spaCy no reconoce nombres poco comunes)
        heuristic_names = self._detect_uppercase_names(text, page)

        # Combinar todas las fuentes
        all_entities = semantic_entities + regex_entities + heuristic_names

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
            if ent.entity_type == "DIRECCION":
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

    def _load_spacy_fallback(self, model_name: str) -> None:
        """Carga spaCy como fallback cuando Ollama no está disponible."""
        try:
            import spacy
            self._spacy_nlp = spacy.load(model_name)
            logger.info("spaCy '%s' cargado como fallback.", model_name)
        except (OSError, ImportError) as exc:
            logger.error("No se pudo cargar spaCy: %s", exc)
            self._spacy_nlp = None

    def _resolve_active_types(self) -> set[SensitiveDataType]:
        """Calcula el conjunto de tipos activos según la configuración."""
        active: set[SensitiveDataType] = set()
        config_dict = self._config.model_dump()
        for field_name, data_type in _TYPE_CONFIG_MAP.items():
            if config_dict.get(field_name, True):
                active.add(data_type)
        return active

    def _detect_with_spacy(self, text: str, page: int) -> list[DetectedEntity]:
        """Fallback: usa spaCy para detectar PER y LOC."""
        if self._spacy_nlp is None:
            return []

        import unicodedata

        _SPACY_LABEL_MAP = {
            "PER": SensitiveDataType.NOMBRE,
            "LOC": SensitiveDataType.DIRECCION,
        }

        entities: list[DetectedEntity] = []

        # Pasada 1: texto original
        doc = self._spacy_nlp(text)
        for ent in doc.ents:
            data_type = _SPACY_LABEL_MAP.get(ent.label_)
            if data_type is None:
                continue
            entities.append(DetectedEntity(
                text=ent.text,
                entity_type=data_type,
                start=ent.start_char,
                end=ent.end_char,
                confidence=0.85,
                page=page,
            ))

        # Pasada 2: texto normalizado (sin acentos, title case)
        def remove_accents(s: str) -> str:
            nfkd = unicodedata.normalize("NFKD", s)
            return "".join(c for c in nfkd if not unicodedata.combining(c))

        lines = text.split("\n")
        offset = 0
        for line in lines:
            if not line.strip():
                offset += len(line) + 1
                continue
            normalized = remove_accents(line).title()
            if normalized != line:
                doc_norm = self._spacy_nlp(normalized)
                for ent in doc_norm.ents:
                    data_type = _SPACY_LABEL_MAP.get(ent.label_)
                    if data_type is None:
                        continue
                    start = offset + ent.start_char
                    end = offset + ent.end_char
                    if end > len(text) or start >= len(text):
                        continue
                    original_text = text[start:end]
                    if original_text.strip():
                        entities.append(DetectedEntity(
                            text=original_text,
                            entity_type=data_type,
                            start=start,
                            end=end,
                            confidence=0.80,
                            page=page,
                        ))
            offset += len(line) + 1

        return entities

    def _filter_by_active_types(
        self, entities: list[DetectedEntity]
    ) -> list[DetectedEntity]:
        """Filtra entidades manteniendo solo las de tipos activos.

        Los tipos del enum SensitiveDataType se filtran según la config.
        Los tipos custom (strings no en el enum) siempre pasan.

        Args:
            entities: Lista de entidades a filtrar.

        Returns:
            Lista filtrada con solo tipos activos.
        """
        # Tipos que están en el enum y no están activos
        _enum_values = {e.value for e in SensitiveDataType}

        return [
            e for e in entities
            if e.entity_type in self._active_types
            or e.entity_type not in _enum_values
        ]

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
        aplica heurísticas de prioridad:
        1. FECHA con formato claro (contiene / o -) siempre gana sobre DNI
        2. Si no hay heurística aplicable, se conserva la de mayor confianza.

        Args:
            entities: Lista de entidades potencialmente solapadas.

        Returns:
            Lista sin solapamientos, conservando la más apropiada.
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
                    winner = self._pick_winner(entity, accepted)
                    if winner is not accepted:
                        resolved.remove(accepted)
                        resolved.append(winner)
                    overlaps = True
                    break

            if not overlaps:
                resolved.append(entity)

        return sorted(resolved, key=lambda e: e.start)

    @staticmethod
    def _pick_winner(
        a: DetectedEntity, b: DetectedEntity
    ) -> DetectedEntity:
        """Elige la entidad ganadora cuando dos se solapan.

        Aplica heurísticas de formato antes de caer a comparación
        de confianza pura.

        Reglas:
        - FECHA con separadores (/ o -) gana sobre DNI porque un DNI
          nunca contiene barras ni guiones internos entre dígitos.
        - CUENTA_BANCARIA con formato X-X-X gana sobre FECHA.
        - En ausencia de heurística, gana la de mayor confianza.
        """
        import re as _re

        # Heurística: FECHA con separadores gana sobre DNI
        fecha_pattern = _re.compile(r"^\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}$")

        # Si una es FECHA con formato claro y la otra es DNI, FECHA gana
        if (
            a.entity_type == SensitiveDataType.FECHA
            and b.entity_type == SensitiveDataType.DNI
            and fecha_pattern.match(a.text)
        ):
            return a
        if (
            b.entity_type == SensitiveDataType.FECHA
            and a.entity_type == SensitiveDataType.DNI
            and fecha_pattern.match(b.text)
        ):
            return b

        # Heurística: CUENTA_BANCARIA con guiones gana sobre FECHA
        cuenta_pattern = _re.compile(r"^\d{4}\-\d{5,6}\-\d{4,5}$")
        if (
            a.entity_type == SensitiveDataType.CUENTA_BANCARIA
            and b.entity_type == SensitiveDataType.FECHA
            and cuenta_pattern.match(a.text)
        ):
            return a
        if (
            b.entity_type == SensitiveDataType.CUENTA_BANCARIA
            and a.entity_type == SensitiveDataType.FECHA
            and cuenta_pattern.match(b.text)
        ):
            return b

        # Default: mayor confianza gana
        return a if a.confidence >= b.confidence else b

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

                # Nunca fusionar entidades FECHA: cada fecha es una
                # unidad atómica (ej: "18/11/25" no debe fusionarse
                # con "27/11/25" aunque estén cerca)
                if current.entity_type == SensitiveDataType.FECHA:
                    should_merge = False

                if should_merge and (
                    "\n" in last.text or "\n" in current.text
                ):
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

    def _detect_uppercase_names(self, text: str, page: int) -> list[DetectedEntity]:
        """Detecta nombres propios en líneas completamente en mayúsculas.

        Heurística: una línea con 2-5 palabras en mayúsculas, sin números,
        sin palabras comunes (SOLUTIONS, ARCHITECT, etc.) es probablemente
        un nombre completo. Común en CVs y documentos formales.

        Args:
            text: Texto a analizar.
            page: Número de página.

        Returns:
            Lista de entidades detectadas como nombres.
        """
        # Palabras comunes que NO son nombres (títulos, roles, etc.)
        _NON_NAME_WORDS = {
            "SOLUTIONS", "ARCHITECT", "ENGINEER", "MANAGER", "DIRECTOR",
            "SENIOR", "JUNIOR", "LEAD", "HEAD", "CHIEF", "OFFICER",
            "CONSULTANT", "SPECIALIST", "ANALYST", "DEVELOPER", "DESIGNER",
            "PROFESSIONAL", "EXECUTIVE", "SUMMARY", "EXPERIENCE", "EDUCATION",
            "SKILLS", "CONTACT", "LANGUAGES", "VISION", "CONFIDENTIAL",
            "WORK", "TECHNICAL", "CERTIFICATIONS", "COURSES", "PRODUCTS",
            "INTEGRATION", "SYSTEM", "SYSTEMS", "PROGRAMMING", "DATABASE",
            "SECURITY", "MIDDLEWARE", "CLOUD", "PLATFORM", "SERVICES",
            "SOFT", "HARD", "FORMULARIO", "CONTRATO", "FICHA", "REGISTRO",
            "DATOS", "PERSONALES", "INFORMACION", "LABORAL", "FINANCIEROS",
            "OBSERVACIONES", "CLAUSULAS", "PARTES", "INTERVINIENTES",
            "PRESTADOR", "EMPLEADO", "AREA", "CARGO", "MODALIDAD",
            "COMPLEJO", "EDUCACIONAL", "ENSEÑANZA", "MEDIA", "ANALISTA",
            "PROGRAMADOR", "API", "IBM", "IT", "PRODUCT",
        }

        entities: list[DetectedEntity] = []
        lines = text.split("\n")
        offset = 0

        for line in lines:
            stripped = line.strip()
            offset_start = text.find(line, offset)
            if offset_start == -1:
                offset += len(line) + 1
                continue

            # Verificar: línea en mayúsculas, 2-5 palabras, sin números
            words = stripped.split()
            if (
                2 <= len(words) <= 5
                and stripped == stripped.upper()
                and stripped.replace(" ", "").isalpha()
                and not any(w in _NON_NAME_WORDS for w in words)
                and all(len(w) >= 2 for w in words)
            ):
                # Parece un nombre completo
                start = offset_start + (len(line) - len(line.lstrip()))
                end = start + len(stripped)
                entities.append(DetectedEntity(
                    text=stripped,
                    entity_type=SensitiveDataType.NOMBRE,
                    start=start,
                    end=end,
                    confidence=0.80,
                    page=page,
                ))
            # También detectar líneas en Title Case (firmas)
            # Ej: "Gustavo Ariel Vilas" como línea sola
            elif (
                2 <= len(words) <= 4
                and stripped.replace(" ", "").isalpha()
                and all(w[0].isupper() and w[1:].islower() for w in words if len(w) > 1)
                and not any(w.upper() in _NON_NAME_WORDS for w in words)
                and all(len(w) >= 2 for w in words)
                and len(stripped) <= 40
            ):
                start = offset_start + (len(line) - len(line.lstrip()))
                end = start + len(stripped)
                entities.append(DetectedEntity(
                    text=stripped,
                    entity_type=SensitiveDataType.NOMBRE,
                    start=start,
                    end=end,
                    confidence=0.78,
                    page=page,
                ))

            offset = offset_start + len(line) + 1

        return entities

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
