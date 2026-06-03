"""Motor de detección por patrones regex.

Combina:
1. Patrones base hardcodeados (DNI contextual, FECHA, CUIT, etc.)
2. Patrones dinámicos desde custom_types en types_config.json
"""

from __future__ import annotations

import logging
import re

from app.models import DetectedEntity, SensitiveDataType

logger = logging.getLogger(__name__)

# Confianza fija para matches regex exactos
REGEX_CONFIDENCE = 0.95

# Meses en español para detección de fechas textuales
_MESES_ES = (
    "enero|febrero|marzo|abril|mayo|junio|"
    "julio|agosto|septiembre|octubre|noviembre|diciembre"
)

# --- DNI contextual ---

_DNI_CONTEXT_KEYWORDS = (
    r"(?:"
    r"DNI|D\.N\.I\.?|D\.N\.I|"
    r"Documento|Doc\.?|"
    r"Documento\s+Nacional\s+de\s+Identidad|"
    r"Nro\.?\s*(?:de\s+)?(?:Doc(?:umento)?|DNI)|"
    r"N[°ºúu]mero\s+de\s+(?:Doc(?:umento)?|DNI)|"
    r"Identidad|"
    r"Socio|Titular|"
    r"Nro\.?\s*Socio"
    r")"
)

_DNI_CONTEXT_PATTERN = re.compile(
    _DNI_CONTEXT_KEYWORDS + r"[:\s\-\.Nº°#]{0,15}(\d{2}\.?\d{3}\.?\d{2,3})\b",
    re.IGNORECASE,
)

_DNI_DOTTED_PATTERN = re.compile(
    r"\b(\d{1,2}\.\d{3}\.\d{3})\b"
)

# --- Patrones base compilados ---

_PATTERNS: list[tuple[re.Pattern[str], SensitiveDataType]] = [
    # CUIT/CUIL
    (
        re.compile(r"\b(20|23|24|27|30|33|34)\-?\d{8}\-?\d\b"),
        SensitiveDataType.CUIT_CUIL,
    ),
    # Teléfono internacional
    (
        re.compile(r"\+\d{1,3}\s?\d[\d\s\-]{7,14}\d"),
        SensitiveDataType.TELEFONO,
    ),
    # Celular argentino
    (
        re.compile(r"\+54\s?9\s?\d[\d\s\-]{8,14}\d"),
        SensitiveDataType.CELULAR,
    ),
    # Email
    (
        re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"),
        SensitiveDataType.EMAIL,
    ),
    # Tarjeta de crédito 16 dígitos (Visa, Mastercard, Discover, JCB)
    (
        re.compile(r"\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b"),
        SensitiveDataType.TARJETA_CREDITO,
    ),
    # Tarjeta American Express 15 dígitos (prefijo 34/37)
    (
        re.compile(r"\b3[47]\d{2}[\s\-]?\d{6}[\s\-]?\d{5}\b"),
        SensitiveDataType.TARJETA_CREDITO,
    ),
    # Pasaporte argentino
    (
        re.compile(r"\bAA[A-Z]?\d{6}\b"),
        SensitiveDataType.PASAPORTE,
    ),
    # Cuenta bancaria CBU (22 dígitos)
    (
        re.compile(r"\b\d{22}\b"),
        SensitiveDataType.CUENTA_BANCARIA,
    ),
    # Número de cuenta con guiones (4-5/6-4/5)
    (
        re.compile(r"\b\d{4}\-\d{5,6}\-\d{4,5}\b"),
        SensitiveDataType.CUENTA_BANCARIA,
    ),
    # Fecha DD/MM/AAAA o DD/MM/AA
    (
        re.compile(r"\b\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}\b"),
        SensitiveDataType.FECHA,
    ),
    # Fecha textual en español
    (
        re.compile(
            r"\b\d{1,2}\s+de\s+(?:" + _MESES_ES + r")\s+(?:de\s+)?\d{4}\b",
            re.IGNORECASE,
        ),
        SensitiveDataType.FECHA,
    ),
    # Expediente GEDO/TAD
    (
        re.compile(r"\bEX-\d{4}-\d{6,10}-[A-Z]{2,4}-[A-Z0-9#]+\b"),
        "EXPEDIENTE",
    ),
]

# --- Direcciones ---

_ADDRESS_WITH_KEYWORD = re.compile(
    r"(?:calle|Calle|CALLE|av\.?|Av\.?|AV\.?|avenida|Avenida|"
    r"domicilio|Domicilio|dirección|Dirección|sitos?\s+en\s+(?:la\s+)?(?:calle)?)"
    r"\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñA-ZÁÉÍÓÚÑ\s]+\d{1,5}(?:[/\-]\d{1,4})?(?:\s*,?\s*(?:CABA|C\.?A\.?B\.?A\.?|Capital Federal))?)",
    re.IGNORECASE,
)

# --- Nombres con título ---

_NAME_WITH_TITLE = re.compile(
    r"(?:Sr\.?|Sra\.?|Srta\.?|Dr\.?|Dra\.?|Lic\.?|Ing\.?|"
    r"Escriban[oa]|Abog\.?|Prof\.?|Titular|heredero\s+del\s+Sr\.?)"
    r"\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,4})",
    re.UNICODE,
)


def detect_with_regex(text: str, page: int) -> list[DetectedEntity]:
    """Detecta entidades sensibles usando patrones regex base.

    Incluye: DNI contextual, FECHA, CUIT, email, teléfono, tarjeta,
    cuenta bancaria, expediente, direcciones y nombres con título.

    Args:
        text: Texto extraído de una página del PDF.
        page: Número de página donde se encontró el texto.

    Returns:
        Lista de entidades detectadas.
    """
    entities: list[DetectedEntity] = []

    # DNI contextual
    entities.extend(_detect_dni_contextual(text, page))

    # Direcciones con keyword
    entities.extend(_detect_addresses(text, page))

    # Nombres con título
    entities.extend(_detect_names_with_title(text, page))

    # Patrones base
    for pattern, entity_type in _PATTERNS:
        for match in pattern.finditer(text):
            entities.append(DetectedEntity(
                text=match.group(),
                entity_type=entity_type,
                start=match.start(),
                end=match.end(),
                confidence=REGEX_CONFIDENCE,
                page=page,
            ))

    return entities


def detect_with_custom_patterns(
    text: str,
    page: int,
    patterns: list[tuple[re.Pattern[str], str]],
) -> list[DetectedEntity]:
    """Detecta entidades usando patrones regex dinámicos (custom_types).

    Args:
        text: Texto extraído de una página del PDF.
        page: Número de página.
        patterns: Lista de tuplas (regex_compilado, label_tipo).

    Returns:
        Lista de entidades detectadas.
    """
    entities: list[DetectedEntity] = []

    # Primero ejecutar los patrones base
    entities.extend(detect_with_regex(text, page))

    # Luego los custom patterns
    for pattern, entity_type in patterns:
        try:
            for match in pattern.finditer(text):
                entities.append(DetectedEntity(
                    text=match.group(),
                    entity_type=entity_type,
                    start=match.start(),
                    end=match.end(),
                    confidence=REGEX_CONFIDENCE,
                    page=page,
                ))
        except re.error as exc:
            logger.warning(
                "Error ejecutando patrón para tipo '%s': %s",
                entity_type, exc,
            )

    return entities


def compile_patterns_from_config(
    custom_types: list[dict],
) -> list[tuple[re.Pattern[str], str]]:
    """Compila los patrones regex desde custom_types de la config.

    Args:
        custom_types: Lista de diccionarios con id, label, pattern, enabled.

    Returns:
        Lista de tuplas (regex_compilado, label) listas para usar.
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
                ct.get("id"), exc, pattern_str,
            )

    return compiled


# --- Funciones privadas ---

def _detect_dni_contextual(text: str, page: int) -> list[DetectedEntity]:
    """Detecta DNI solo con contexto explícito o formato puntuado."""
    entities: list[DetectedEntity] = []
    seen: set[tuple[int, int]] = set()

    for match in _DNI_CONTEXT_PATTERN.finditer(text):
        dni_text = match.group(1)
        start = match.start(1)
        end = match.end(1)
        if (start, end) not in seen:
            seen.add((start, end))
            entities.append(DetectedEntity(
                text=dni_text, entity_type=SensitiveDataType.DNI,
                start=start, end=end, confidence=0.97, page=page,
            ))

    for match in _DNI_DOTTED_PATTERN.finditer(text):
        dni_text = match.group(1)
        start = match.start(1)
        end = match.end(1)
        if (start, end) not in seen:
            seen.add((start, end))
            entities.append(DetectedEntity(
                text=dni_text, entity_type=SensitiveDataType.DNI,
                start=start, end=end, confidence=REGEX_CONFIDENCE, page=page,
            ))

    return entities


def _detect_addresses(text: str, page: int) -> list[DetectedEntity]:
    """Detecta direcciones con formato calle + número."""
    entities: list[DetectedEntity] = []
    for match in _ADDRESS_WITH_KEYWORD.finditer(text):
        addr = match.group(1).strip()
        if len(addr) < 5:
            continue
        entities.append(DetectedEntity(
            text=addr, entity_type=SensitiveDataType.DIRECCION,
            start=match.start(1), end=match.end(1),
            confidence=0.92, page=page,
        ))
    return entities


def _detect_names_with_title(text: str, page: int) -> list[DetectedEntity]:
    """Detecta nombres precedidos por títulos (Sr., Escribana, etc.)."""
    _NON_NAMES = {
        "Argentina", "Buenos Aires", "Capital Federal",
        "Administración", "Declaración", "Manifestación",
    }
    entities: list[DetectedEntity] = []
    for match in _NAME_WITH_TITLE.finditer(text):
        name = match.group(1).strip()
        if len(name) < 4 or name in _NON_NAMES:
            continue
        entities.append(DetectedEntity(
            text=name, entity_type=SensitiveDataType.NOMBRE,
            start=match.start(1), end=match.end(1),
            confidence=0.92, page=page,
        ))
    return entities
