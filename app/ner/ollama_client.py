"""Cliente para comunicación con Ollama API local.

Envía texto al modelo Llama 3.1 8B para detectar nombres
y direcciones que los patrones regex no pueden capturar.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from app.models import DetectedEntity, SensitiveDataType

logger = logging.getLogger(__name__)

# Defaults — se sobreescriben con config/ollama.json si existe
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3.1:8b"
OLLAMA_TIMEOUT = 60.0  # segundos
OLLAMA_KEEP_ALIVE = "10m"


def _load_ollama_config() -> dict:
    """Carga la configuración de Ollama desde config/ollama.json."""
    from pathlib import Path

    config_path = Path(__file__).resolve().parent.parent.parent / "config" / "ollama.json"
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
        return data
    except Exception:
        return {}


def get_ollama_model() -> str:
    """Retorna el modelo configurado."""
    config = _load_ollama_config()
    return config.get("model", OLLAMA_MODEL)


def get_ollama_temperature() -> float:
    """Retorna la temperatura configurada."""
    config = _load_ollama_config()
    return config.get("temperature", 0.1)


def _normalize_type(type_str: str) -> str:
    """Normaliza un nombre de tipo removiendo acentos y pasando a upper.

    Permite que ORGANIZACIÓN == ORGANIZACION, MONTO_MONEY == MONTO_MONEY, etc.
    """
    import unicodedata
    nfkd = unicodedata.normalize("NFKD", type_str)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).upper()

# Prompt para detección de PII
NER_PROMPT = """Analiza el siguiente texto y extrae TODOS los datos personales sensibles.

Devuelve SOLO un JSON array con los datos encontrados. Cada elemento debe tener:
- "text": el texto exacto encontrado (tal cual aparece)
- "type": uno de: NOMBRE, DIRECCION

Reglas:
- NOMBRE: nombres completos de personas (nombre + apellido). Incluye nombres en MAYÚSCULAS.
- DIRECCION: direcciones postales, ciudades con país (ej: "Santiago, Chile"), calles con número.
- NO incluyas: títulos de cargo, nombres de empresas, tecnologías, idiomas.
- Si no hay datos sensibles, devuelve un array vacío: []

Texto a analizar:
---
{text}
---

Responde SOLO con el JSON array, sin explicaciones:"""


def is_ollama_available() -> bool:
    """Verifica si Ollama está corriendo y el modelo está disponible."""
    status = get_ollama_status()
    return status["available"]


def get_ollama_status() -> dict:
    """Retorna estado detallado de Ollama con razón si no está disponible."""
    try:
        response = httpx.get(
            f"{OLLAMA_BASE_URL}/api/tags",
            timeout=5.0,
        )
        if response.status_code != 200:
            return {
                "available": False,
                "reason": "Ollama respondió con error",
                "service_running": True,
                "model_ready": False,
            }
        data = response.json()
        models = [m.get("name", "") for m in data.get("models", [])]
        has_model = any("llama3.1" in m for m in models)
        if has_model:
            return {
                "available": True,
                "reason": None,
                "service_running": True,
                "model_ready": True,
            }
        else:
            return {
                "available": False,
                "reason": f"Modelo llama3.1:8b no descargado. Ejecute: ollama pull llama3.1:8b. Modelos disponibles: {models}",
                "service_running": True,
                "model_ready": False,
            }
    except httpx.ConnectError:
        return {
            "available": False,
            "reason": "Ollama no está corriendo. Ejecute: ollama serve",
            "service_running": False,
            "model_ready": False,
        }
    except httpx.TimeoutException:
        return {
            "available": False,
            "reason": "Ollama no responde (timeout). Reinicie Ollama.",
            "service_running": False,
            "model_ready": False,
        }
    except Exception as exc:
        return {
            "available": False,
            "reason": f"Error: {exc}",
            "service_running": False,
            "model_ready": False,
        }


def detect_with_ollama(
    text: str, page: int, prompt_template: str | None = None,
    ignored_types: set[str] | None = None,
    temperature: float = 0.1,
) -> list[DetectedEntity]:
    """Detecta nombres y direcciones usando Ollama (Llama 3.1 8B).

    Envía el texto al modelo local y parsea la respuesta JSON
    para extraer entidades de tipo NOMBRE y DIRECCION.

    Args:
        text: Texto a analizar.
        page: Número de página.
        prompt_template: Prompt personalizado con placeholder {text}.
            Si no se proporciona, usa NER_PROMPT por defecto.
        ignored_types: Conjunto de tipos a ignorar de la respuesta de Ollama.
        temperature: Temperatura del modelo (0.0-1.0). Menor = más determinístico.

    Returns:
        Lista de entidades detectadas. Lista vacía si Ollama
        no está disponible o hay un error.
    """
    if not text.strip():
        return []

    # Truncar texto muy largo para evitar timeouts
    max_chars = 8000
    truncated = text[:max_chars] if len(text) > max_chars else text

    template = prompt_template if prompt_template else NER_PROMPT

    # Formatear el prompt - soportar múltiples placeholders
    try:
        if "{text}" in template:
            prompt = template.format(text=truncated)
        elif "{texto_del_documento}" in template:
            prompt = template.format(texto_del_documento=truncated)
        elif "{texto}" in template:
            prompt = template.format(texto=truncated)
        else:
            # Si no tiene placeholder conocido, agregar el texto al final
            prompt = template + "\n" + truncated
    except (KeyError, ValueError) as exc:
        logger.error("Error al formatear prompt de Ollama: %s. Usando prompt por defecto.", exc)
        prompt = NER_PROMPT.format(text=truncated)

    try:
        # Cargar config dinámica
        ollama_cfg = _load_ollama_config()
        model = ollama_cfg.get("model", OLLAMA_MODEL)
        base_url = ollama_cfg.get("base_url", OLLAMA_BASE_URL)
        keep_alive = ollama_cfg.get("keep_alive", OLLAMA_KEEP_ALIVE)
        num_ctx = ollama_cfg.get("num_ctx", 4096)
        num_predict = ollama_cfg.get("num_predict", 1024)
        timeout = ollama_cfg.get("timeout_seconds", OLLAMA_TIMEOUT)
        # Si no se pasa temperature explícito, usar el de la config
        temp = temperature if temperature != 0.1 else ollama_cfg.get("temperature", 0.1)

        response = httpx.post(
            f"{base_url}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "keep_alive": keep_alive,
                "options": {
                    "temperature": temp,
                    "num_predict": num_predict,
                    "num_ctx": num_ctx,
                },
            },
            timeout=timeout,
        )

        if response.status_code != 200:
            logger.warning("Ollama respondió con status %d", response.status_code)
            return []

        data = response.json()
        raw_response = data.get("response", "").strip()

        return _parse_ollama_response(raw_response, text, page, ignored_types)

    except httpx.ConnectError:
        logger.warning("No se pudo conectar a Ollama en %s", OLLAMA_BASE_URL)
        return []
    except httpx.TimeoutException:
        logger.warning("Timeout al comunicarse con Ollama")
        return []
    except Exception as exc:
        logger.warning("Error inesperado con Ollama: %s", exc)
        return []


def _parse_ollama_response(
    raw_response: str, original_text: str, page: int,
    ignored_types: set[str] | None = None,
) -> list[DetectedEntity]:
    """Parsea la respuesta JSON de Ollama y mapea posiciones al texto original.

    Args:
        raw_response: Respuesta cruda del modelo (debería ser JSON array).
        original_text: Texto original para buscar posiciones.
        page: Número de página.
        ignored_types: Conjunto de tipos a descartar (falsos positivos comunes).

    Returns:
        Lista de DetectedEntity con posiciones mapeadas al texto original.
    """
    # Intentar extraer JSON del response (a veces viene con texto extra)
    json_str = raw_response
    # Buscar el array JSON en la respuesta
    start_idx = raw_response.find("[")
    end_idx = raw_response.rfind("]")
    if start_idx != -1 and end_idx != -1:
        json_str = raw_response[start_idx:end_idx + 1]

    try:
        items = json.loads(json_str)
    except json.JSONDecodeError:
        logger.debug("No se pudo parsear respuesta de Ollama como JSON: %s", raw_response[:200])
        return []

    if not isinstance(items, list):
        return []

    entities: list[DetectedEntity] = []

    for item in items:
        if not isinstance(item, dict):
            continue

        entity_text = item.get("text", "").strip()
        entity_type_str = item.get("type", "").upper()

        if not entity_text:
            continue

        # Mapear tipos conocidos, pero aceptar cualquier tipo que Ollama devuelva
        known_types = {
            "NOMBRE": "NOMBRE",
            "DIRECCION": "DIRECCION",
            "EMAIL": "EMAIL",
            "TELEFONO": "TELEFONO",
            "CELULAR": "CELULAR",
            "DNI": "DNI",
            "DNI_DOCUMENTO": "DNI",
            "DATOS_BANCARIOS": "CUENTA_BANCARIA",
            "TARJETA_CREDITO": "TARJETA_CREDITO",
            "CUENTA_BANCARIA": "CUENTA_BANCARIA",
            "CUIT_CUIL": "CUIT_CUIL",
            "PASAPORTE": "PASAPORTE",
            "FECHA_NACIMIENTO": "FECHA",
            "FECHAS": "FECHA",
            "FECHA": "FECHA",
            "IP_DISPOSITIVO": "IP_DISPOSITIVO",
        }

        if not entity_type_str:
            continue

        # Descartar tipos que Ollama inventa y no son datos sensibles.
        # La lista se carga desde ignored_ollama_types en la config.
        # Normalizar sin acentos para comparar (ORGANIZACIÓN == ORGANIZACION)
        if ignored_types and _normalize_type(entity_type_str) in ignored_types:
            continue

        # Usar el mapeo si existe, sino usar el tipo tal cual
        final_type = known_types.get(entity_type_str, entity_type_str)

        # Buscar la posición del texto en el original
        # Buscar case-insensitive para manejar mayúsculas/minúsculas
        pos = original_text.find(entity_text)
        if pos == -1:
            # Intentar búsqueda case-insensitive
            lower_text = original_text.lower()
            lower_entity = entity_text.lower()
            pos = lower_text.find(lower_entity)
            if pos != -1:
                # Usar el texto original en esa posición
                entity_text = original_text[pos:pos + len(entity_text)]

        if pos == -1:
            # No se encontró en el texto — skip
            continue

        entities.append(DetectedEntity(
            text=entity_text,
            entity_type=final_type,
            start=pos,
            end=pos + len(entity_text),
            confidence=0.90,
            page=page,
        ))

    return entities
