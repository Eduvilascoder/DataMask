"""Motor de detección por patrones regex.

TODOS los patrones se cargan desde types_config.json (types + custom_types).
No hay patrones hardcodeados — todo es editable desde la UI de Configuración.
"""

from __future__ import annotations

import logging
import re

from app.models import DetectedEntity, SensitiveDataType

logger = logging.getLogger(__name__)

# Confianza fija para matches regex exactos
REGEX_CONFIDENCE = 0.95


def detect_with_custom_patterns(
    text: str,
    page: int,
    patterns: list[tuple[re.Pattern[str], str]],
) -> list[DetectedEntity]:
    """Detecta entidades sensibles usando los patrones de la config.

    Ejecuta todos los patrones (base + custom) y retorna las
    entidades detectadas.

    Args:
        text: Texto extraído de una página del PDF.
        page: Número de página.
        patterns: Lista de tuplas (regex_compilado, label_tipo).

    Returns:
        Lista de entidades detectadas.
    """
    entities: list[DetectedEntity] = []

    for pattern, entity_type in patterns:
        try:
            for match in pattern.finditer(text):
                # Extraer el texto capturado:
                # Si hay grupos, usar el primer grupo no-None
                # Si no hay grupos, usar el match completo
                captured = None
                start = match.start()
                end = match.end()

                if match.lastindex:
                    for i in range(1, match.lastindex + 1):
                        if match.group(i) is not None:
                            captured = match.group(i)
                            start = match.start(i)
                            end = match.end(i)
                            break

                if captured is None:
                    captured = match.group()
                    start = match.start()
                    end = match.end()

                if not captured or not captured.strip():
                    continue

                entities.append(DetectedEntity(
                    text=captured,
                    entity_type=entity_type,
                    start=start,
                    end=end,
                    confidence=REGEX_CONFIDENCE,
                    page=page,
                ))
        except re.error as exc:
            logger.warning(
                "Error ejecutando patrón para tipo '%s': %s",
                entity_type, exc,
            )

    return entities


def detect_with_regex(text: str, page: int) -> list[DetectedEntity]:
    """Fallback: retorna lista vacía.

    Los patrones base ahora se cargan desde la config.
    Esta función existe solo por compatibilidad con tests.
    """
    return []


def compile_patterns_from_config(
    custom_types: list[dict],
) -> list[tuple[re.Pattern[str], str]]:
    """Compila patrones regex desde custom_types de la config.

    Args:
        custom_types: Lista de diccionarios con id/label, pattern, enabled.

    Returns:
        Lista de tuplas (regex_compilado, label).
    """
    compiled: list[tuple[re.Pattern[str], str]] = []

    for ct in custom_types:
        if not ct.get("enabled", False):
            continue
        pattern_str = ct.get("pattern")
        if not pattern_str:
            continue

        label = ct.get("label", ct.get("id", "UNKNOWN")).upper()
        flags = re.IGNORECASE if ct.get("case_insensitive", False) else 0

        try:
            compiled_pattern = re.compile(pattern_str, flags)
            compiled.append((compiled_pattern, label))
        except re.error as exc:
            logger.error(
                "Error compilando patrón '%s': %s. Regex: '%s'",
                ct.get("id", label), exc, pattern_str,
            )

    return compiled


def compile_all_patterns_from_config(
    raw_config: dict,
) -> list[tuple[re.Pattern[str], str]]:
    """Compila TODOS los patrones: types base + custom_types.

    Lee el campo 'pattern' de cada type habilitado en 'types'
    y también de cada custom_type habilitado.

    Args:
        raw_config: Diccionario completo de types_config.json

    Returns:
        Lista de tuplas (regex_compilado, label) de todos los tipos.
    """
    compiled: list[tuple[re.Pattern[str], str]] = []

    # 1. Tipos base (de "types")
    types = raw_config.get("types", {})
    for key, type_data in types.items():
        if not type_data.get("enabled", True):
            continue
        pattern_str = type_data.get("pattern")
        if not pattern_str:
            continue

        label = type_data.get("label", key.upper())
        # Fechas textuales necesitan IGNORECASE
        flags = re.IGNORECASE if key in ("fecha", "direccion", "dni") else 0

        try:
            compiled_pattern = re.compile(pattern_str, flags)
            compiled.append((compiled_pattern, label))
        except re.error as exc:
            logger.error(
                "Error compilando patrón de tipo '%s': %s. Regex: '%s'",
                key, exc, pattern_str,
            )

    # 2. Custom types
    custom_types = raw_config.get("custom_types", [])
    compiled.extend(compile_patterns_from_config(custom_types))

    logger.info(
        "Cargados %d patrones regex desde config (types: %d, custom: %d).",
        len(compiled),
        len(compiled) - len([c for c in custom_types if c.get("enabled") and c.get("pattern")]),
        len([c for c in custom_types if c.get("enabled") and c.get("pattern")]),
    )
    return compiled
