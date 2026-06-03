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

# Palabras clave que preceden a un DNI real (case-insensitive)
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

# Regex DNI con contexto: requiere una palabra clave dentro de los
# 40 caracteres previos al número
_DNI_CONTEXT_PATTERN = re.compile(
    _DNI_CONTEXT_KEYWORDS + r"[:\s\-\.Nº°#]{0,15}(\d{2}\.?\d{3}\.?\d{2,3})\b",
    re.IGNORECASE,
)

# DNI con puntos explícitos (XX.XXX.XXX) — esto casi siempre es un DNI
# y no un número de referencia genérico
_DNI_DOTTED_PATTERN = re.compile(
    r"\b(\d{1,2}\.\d{3}\.\d{3})\b"
)

# Patrones regex compilados para cada tipo de dato sensible
_PATTERNS: list[tuple[re.Pattern[str], SensitiveDataType]] = [
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
    # Tarjeta de crédito: 16 dígitos agrupados de a 4 (Visa, Mastercard, etc.)
    (
        re.compile(r"\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b"),
        SensitiveDataType.TARJETA_CREDITO,
    ),
    # Tarjeta American Express: 15 dígitos en formato 4-6-5, prefijo 34xx o 37xx
    (
        re.compile(r"\b3[47]\d{2}[\s\-]?\d{6}[\s\-]?\d{5}\b"),
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
    # Excluye lo que ya matcheó como tarjeta Amex (prefijos 34xx, 37xx)
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
    # Expediente GEDO/TAD: EX-2025-12345678-APN-SCEYM#MEC
    (
        re.compile(
            r"\bEX-\d{4}-\d{6,10}-[A-Z]{2,4}-[A-Z0-9#]+\b"
        ),
        "EXPEDIENTE",
    ),
    # Expediente judicial: "Expte. Nº 12345/2024", "Expediente N° 1234/24"
    (
        re.compile(
            r"\b(?:Expte\.?|Expediente|Exp\.?)\s*"
            r"(?:N[°ºo]\.?|Nro\.?|Número)?\s*"
            r"(\d{1,8}[/\-]\d{2,4})\b",
            re.IGNORECASE,
        ),
        "EXPEDIENTE",
    ),
    # Expediente administrativo provincial: EXP-S01:0001234/2024
    (
        re.compile(
            r"\bEXP-[A-Z]\d{2}:\d{4,8}/\d{2,4}\b"
        ),
        "EXPEDIENTE",
    ),
    # Expediente con formato IF/NO/PV (informes, notas, providencias GEDO)
    # IF-2025-12345678-APN-XXX#YYY, NO-2025-12345678-APN-XXX#YYY
    (
        re.compile(
            r"\b(?:IF|NO|PV|DI|RS|RE|ME|AC|TRI|DOCFI)-\d{4}-\d{6,10}-[A-Z]{2,4}-[A-Z0-9#]+\b"
        ),
        "EXPEDIENTE",
    ),
    # Expediente con caratulación: "Actuación Nº 12345-1234/2024"
    (
        re.compile(
            r"\b(?:Actuación|Causa|Legajo|Sumario)\s*"
            r"(?:N[°ºo]\.?|Nro\.?)?\s*"
            r"(\d{1,8}(?:-\d{1,6})?/\d{2,4})\b",
            re.IGNORECASE,
        ),
        "EXPEDIENTE",
    ),
]


def detect_with_regex(text: str, page: int) -> list[DetectedEntity]:
    """Detecta entidades sensibles en el texto usando patrones regex.

    Ejecuta todos los patrones regex definidos para formatos argentinos
    y retorna las entidades detectadas con confianza fija de 0.95.

    Para DNI aplica detección contextual: solo detecta un número de
    7-8 dígitos como DNI si está precedido por palabras clave como
    "DNI", "Documento", "Socio", etc., o si tiene formato con puntos
    explícitos (XX.XXX.XXX).

    Args:
        text: Texto extraído de una página del PDF.
        page: Número de página donde se encontró el texto.

    Returns:
        Lista de entidades detectadas con tipo, posición, confianza y página.
    """
    entities: list[DetectedEntity] = []

    # Detección contextual de DNI
    entities.extend(_detect_dni_contextual(text, page))

    # Detección de direcciones con formato calle + número
    entities.extend(_detect_addresses(text, page))

    # Detección de nombres con título/prefijo
    entities.extend(_detect_names_with_title(text, page))

    # Detección de los demás tipos con regex simple
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


def _detect_dni_contextual(text: str, page: int) -> list[DetectedEntity]:
    """Detecta DNI solo cuando hay contexto que lo indica.

    Estrategia:
    1. DNI con contexto explícito: "DNI: 35.123.456", "Documento 35123456"
    2. DNI con formato puntuado: "35.123.456" (siempre es DNI)

    No detecta números de 7-8 dígitos sin contexto (evita falsos positivos
    con números de referencia, códigos de transacción, etc.)

    Args:
        text: Texto a analizar.
        page: Número de página.

    Returns:
        Lista de entidades DNI detectadas con contexto.
    """
    entities: list[DetectedEntity] = []
    seen_positions: set[tuple[int, int]] = set()

    # 1. DNI con palabra clave previa (alta confianza)
    for match in _DNI_CONTEXT_PATTERN.finditer(text):
        # El grupo 1 es el número en sí
        dni_text = match.group(1)
        # Calcular posición real del número dentro del match
        dni_start = match.start(1)
        dni_end = match.end(1)
        pos_key = (dni_start, dni_end)

        if pos_key not in seen_positions:
            seen_positions.add(pos_key)
            entities.append(DetectedEntity(
                text=dni_text,
                entity_type=SensitiveDataType.DNI,
                start=dni_start,
                end=dni_end,
                confidence=0.97,
                page=page,
            ))

    # 2. DNI con formato puntuado explícito (X.XXX.XXX o XX.XXX.XXX)
    # Un número con puntos separadores casi siempre es un DNI
    for match in _DNI_DOTTED_PATTERN.finditer(text):
        dni_text = match.group(1)
        start = match.start(1)
        end = match.end(1)
        pos_key = (start, end)

        if pos_key not in seen_positions:
            seen_positions.add(pos_key)
            entities.append(DetectedEntity(
                text=dni_text,
                entity_type=SensitiveDataType.DNI,
                start=start,
                end=end,
                confidence=REGEX_CONFIDENCE,
                page=page,
            ))

    return entities


# --- Patrones para direcciones con formato calle + número ---

# Palabras que indican una calle/dirección
_STREET_PREFIXES = (
    r"(?:calle|Calle|CALLE|av\.?|Av\.?|AV\.?|avenida|Avenida|"
    r"bv\.?|Bv\.?|boulevard|Boulevard|"
    r"pasaje|Pasaje|pje\.?|"
    r"diagonal|Diagonal)"
)

# Dirección: prefijo de calle + nombre + número
_ADDRESS_PATTERN = re.compile(
    r"(?:" + _STREET_PREFIXES + r"\s+)?"
    r"([A-ZÁÉÍÓÚÑ][a-záéíóúñA-ZÁÉÍÓÚÑ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñA-ZÁÉÍÓÚÑ]*)*)"
    r"\s+(\d{1,5}(?:[/\-]\d{1,4})?)"
    r"(?:\s*,?\s*(?:CABA|C\.?A\.?B\.?A\.?|Capital Federal|Buenos Aires|"
    r"piso\s+\d+|[A-Z]{1,2}|dto\.?\s*\w+))?",
    re.MULTILINE,
)

# Patrón más específico: "calle X NNNN" con keyword explícita
_ADDRESS_WITH_KEYWORD = re.compile(
    r"(?:calle|Calle|CALLE|av\.?|Av\.?|AV\.?|avenida|Avenida|"
    r"domicilio|Domicilio|dirección|Dirección|sitos?\s+en\s+(?:la\s+)?(?:calle)?)"
    r"\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñA-ZÁÉÍÓÚÑ\s]+\d{1,5}(?:[/\-]\d{1,4})?(?:\s*,?\s*(?:CABA|C\.?A\.?B\.?A\.?|Capital Federal))?)",
    re.IGNORECASE,
)

# --- Patrones para nombres con título/prefijo ---

_NAME_WITH_TITLE = re.compile(
    r"(?:Sr\.?|Sra\.?|Srta\.?|Dr\.?|Dra\.?|Lic\.?|Ing\.?|"
    r"Escriban[oa]|Abog\.?|Prof\.?|Titular|heredero\s+del\s+Sr\.?)"
    r"\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,4})",
    re.UNICODE,
)


def _detect_addresses(text: str, page: int) -> list[DetectedEntity]:
    """Detecta direcciones postales con formato calle + número.

    Args:
        text: Texto a analizar.
        page: Número de página.

    Returns:
        Lista de entidades DIRECCION detectadas.
    """
    entities: list[DetectedEntity] = []
    seen_positions: set[tuple[int, int]] = set()

    for match in _ADDRESS_WITH_KEYWORD.finditer(text):
        addr_text = match.group(1).strip()
        start = match.start(1)
        end = match.end(1)
        pos_key = (start, end)

        # Filtrar direcciones que son solo un número o muy cortas
        if len(addr_text) < 5:
            continue

        if pos_key not in seen_positions:
            seen_positions.add(pos_key)
            entities.append(DetectedEntity(
                text=addr_text,
                entity_type=SensitiveDataType.DIRECCION,
                start=start,
                end=end,
                confidence=0.92,
                page=page,
            ))

    return entities


def _detect_names_with_title(text: str, page: int) -> list[DetectedEntity]:
    """Detecta nombres propios precedidos por títulos (Sr., Dra., Escribana, etc.)

    Args:
        text: Texto a analizar.
        page: Número de página.

    Returns:
        Lista de entidades NOMBRE detectadas.
    """
    entities: list[DetectedEntity] = []
    seen_positions: set[tuple[int, int]] = set()

    for match in _NAME_WITH_TITLE.finditer(text):
        name_text = match.group(1).strip()
        start = match.start(1)
        end = match.end(1)
        pos_key = (start, end)

        # Filtrar si es un nombre de empresa o muy corto
        if len(name_text) < 4:
            continue

        # Filtrar palabras que no son nombres
        _NON_NAMES = {
            "Argentina", "Buenos Aires", "Capital Federal",
            "Administración", "Declaración", "Manifestación",
        }
        if name_text in _NON_NAMES:
            continue

        if pos_key not in seen_positions:
            seen_positions.add(pos_key)
            entities.append(DetectedEntity(
                text=name_text,
                entity_type=SensitiveDataType.NOMBRE,
                start=start,
                end=end,
                confidence=0.92,
                page=page,
            ))

    return entities
