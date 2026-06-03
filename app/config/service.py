"""Servicio de configuración persistente de tipos de datos sensibles."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from app.exceptions import ConfigError
from app.models import TypeConfig

logger = logging.getLogger(__name__)


class ConfigService:
    """Gestiona la configuración persistente de tipos de datos sensibles.

    La configuración se almacena en un archivo JSON local que incluye
    metadatos de versión y timestamp de última actualización.
    """

    DEFAULT_CONFIG_PATH = Path("config/types_config.json")
    CURRENT_VERSION = 1

    def __init__(self, config_path: Path | None = None) -> None:
        """Inicializa el servicio de configuración.

        Args:
            config_path: Ruta al archivo de configuración.
                Si es None, usa la ruta por defecto.
        """
        self._config_path = config_path or self.DEFAULT_CONFIG_PATH

    @property
    def config_path(self) -> Path:
        """Ruta al archivo de configuración."""
        return self._config_path

    def load(self) -> TypeConfig:
        """Carga la configuración desde el archivo JSON.

        Si el archivo no existe o está corrupto, retorna la
        configuración por defecto con todos los tipos activos.

        Returns:
            TypeConfig con los valores cargados o defaults.
        """
        if not self._config_path.exists():
            logger.warning(
                "Archivo de configuración no encontrado en '%s'. "
                "Usando configuración por defecto.",
                self._config_path,
            )
            return TypeConfig()

        try:
            raw = self._config_path.read_text(encoding="utf-8")
            data = json.loads(raw)
        except (json.JSONDecodeError, UnicodeDecodeError, OSError) as exc:
            logger.warning(
                "Configuración corrupta o ilegible en '%s': %s. "
                "Usando configuración por defecto.",
                self._config_path,
                exc,
            )
            return TypeConfig()

        return self._parse_config(data)

    def save(self, config: TypeConfig) -> None:
        """Persiste la configuración en el archivo JSON.

        Incluye metadatos de versión y timestamp de actualización.

        Args:
            config: Configuración a persistir.

        Raises:
            ConfigError: Si no se puede escribir el archivo.
        """
        data = {
            "version": self.CURRENT_VERSION,
            "types": config.model_dump(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        try:
            self._config_path.parent.mkdir(parents=True, exist_ok=True)
            self._config_path.write_text(
                json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
        except OSError as exc:
            raise ConfigError(
                code="WRITE_ERROR",
                message=(
                    f"No se pudo escribir la configuración en "
                    f"'{self._config_path}': {exc}"
                ),
                recoverable=True,
            ) from exc

    def validate(self, config: TypeConfig) -> tuple[bool, str | None]:
        """Valida que al menos un tipo de dato sensible esté activo.

        Args:
            config: Configuración a validar.

        Returns:
            Tupla (es_válida, mensaje_error).
            Si es válida, mensaje_error es None.
        """
        values = config.model_dump().values()
        if not any(values):
            return (
                False,
                "Debe existir al menos 1 tipo activo para "
                "realizar el procesamiento.",
            )
        return (True, None)

    def _parse_config(self, data: dict) -> TypeConfig:
        """Parsea el diccionario JSON a TypeConfig.

        Maneja tanto el formato con wrapper 'types' como
        un diccionario plano de campos. Soporta v2+ donde
        cada tipo es un objeto {enabled, label, ...}.

        Args:
            data: Diccionario cargado del JSON.

        Returns:
            TypeConfig parseado, o defaults si los datos son inválidos.
        """
        try:
            types_data = data.get("types", data)
            if not isinstance(types_data, dict):
                logger.warning(
                    "Campo 'types' no es un diccionario. "
                    "Usando configuración por defecto."
                )
                return TypeConfig()

            # v2+: cada tipo es un objeto con campo "enabled"
            # v1: cada tipo es un booleano directamente
            parsed: dict[str, bool] = {}
            for key, val in types_data.items():
                if isinstance(val, dict):
                    parsed[key] = val.get("enabled", True)
                elif isinstance(val, bool):
                    parsed[key] = val
                # Ignorar valores desconocidos

            return TypeConfig(**parsed)
        except (TypeError, ValueError) as exc:
            logger.warning(
                "Error al parsear configuración de tipos: %s. "
                "Usando configuración por defecto.",
                exc,
            )
            return TypeConfig()
