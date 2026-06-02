"""Patrones regex para detección de datos sensibles en formatos argentinos."""

from __future__ import annotations

import re

from app.models import DetectedEntity, SensitiveDataType

# Confianza fija para matches regex exactos
REGEX_CONFIDENCE = 0.95

# Meses en español para detección de fechas textuales
_MESES_ES = (
    "enero|febrero|marzo|abril|mayo|junio|"
    "julio|agosto|septiembre|octubre|noviembre|diciembre"
)

# Patrones regex compilados para cada tipo de dato sensible
_PATTERNS: list[tuple[re.Pattern[str], SensitiveDataType]] = [
    # DNI: 7 u 8 dígitos, opcionalmente separados por puntos (XX.XXX.XXX)
    (
        re.compile(r"\b\d{2}\.?\d{3}\.?\d{3}\b"),
        SensitiveDataType.DNI,
    ),
    # CUIT/CUIL: prefijo (20|23|24|27|30|33|34) + 8 dígitos + 1 dígito verificador
    (
        re.compile(r"\b(20|23|24|27|30|33|34)\-?\d{8}\-?\d\b"),
        SensitiveDataType.CUIT_CUIL,
    ),
    # Teléfono internacional: prefijo + seguido de código de país y dígitos
    # Soporta +54 (Argentina), +56 (Chile), y cualquier prefijo internacional
    (
        re.compile(r"\+\d{1,3}\s?\d[\d\s\-]{7,14}\d"),
        SensitiveDataType.TELEFONO,
    ),
    # Celular: +54 con prefijo 9 para celulares argentinos
    (
        re.compile(r"\+54\s?9\s?\d[\d\s\-]{8,14}\d"),
        SensitiveDataType.CELULAR,
    ),
    # Email: formato estándar de correo electrónico
    (
        re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"),
        SensitiveDataType.EMAIL,
    ),
    # Tarjeta de crédito: 16 dígitos agrupados de a 4
    (
        re.compile(r"\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b"),
        SensitiveDataType.TARJETA_CREDITO,
    ),
    # Pasaporte argentino: AA seguido opcionalmente de una letra y 6 dígitos
    (
        re.compile(r"\bAA[A-Z]?\d{6}\b"),
        SensitiveDataType.PASAPORTE,
    ),
    # Cuenta bancaria CBU: exactamente 22 dígitos
    (
        re.compile(r"\b\d{22}\b"),
        SensitiveDataType.CUENTA_BANCARIA,
    ),
    # Número de cuenta con guiones: formato tipo 3764-575886-12000
    # (4 dígitos, guión, 6 dígitos, guión, 5 dígitos)
    (
        re.compile(r"\b\d{4}\-\d{5,6}\-\d{4,5}\b"),
        SensitiveDataType.CUENTA_BANCARIA,
    ),
    # Fecha DD/MM/AAAA o DD/MM/AA (con / o -)
    (
        re.compile(r"\b\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}\b"),
        SensitiveDataType.FECHA,
    ),
    # Fecha textual en español: "22 de Junio 2025", "4 de agosto de 2025"
    (
        re.compile(
            r"\b\d{1,2}\s+de\s+(?:" + _MESES_ES + r")\s+(?:de\s+)?\d{4}\b",
            re.IGNORECASE,
        ),
        SensitiveDataType.FECHA,
    ),
]


def detect_with_regex(text: str, page: int) -> list[DetectedEntity]:
    """Detecta entidades sensibles en el texto usando patrones regex.

    Ejecuta todos los patrones regex definidos para formatos argentinos
    y retorna las entidades detectadas con confianza fija de 0.95.

    Args:
        text: Texto extraído de una página del PDF.
        page: Número de página donde se encontró el texto.

    Returns:
        Lista de entidades detectadas con tipo, posición, confianza y página.
    """
    entities: list[DetectedEntity] = []

    for pattern, entity_type in _PATTERNS:
        for match in pattern.finditer(text):
            entity = DetectedEntity(
                text=match.group(),
                entity_type=entity_type,
                start=match.start(),
                end=match.end(),
                confidence=REGEX_CONFIDENCE,
                page=page,
            )
            entities.append(entity)

    return entities
