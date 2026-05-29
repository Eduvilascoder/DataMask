"""Servicio de registro de auditoría en formato JSON Lines."""

from __future__ import annotations

import getpass
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from app.models import AuditLogEntry


class LogService:
    """Gestiona el registro de auditoría.

    Escribe y lee entradas de log en formato JSON Lines (una entrada
    por línea) en el archivo log/audit.jsonl.
    """

    LOG_DIR = "log"
    LOG_FILE = "audit.jsonl"
    MAX_PAGE_SIZE = 100

    def __init__(self, base_path: str | None = None) -> None:
        """Inicializa el servicio de log.

        Args:
            base_path: Ruta base del proyecto. Si es None, usa el
                directorio de trabajo actual.
        """
        if base_path is None:
            base_path = os.getcwd()
        self._log_dir = Path(base_path) / self.LOG_DIR
        self._log_file = self._log_dir / self.LOG_FILE

    def _ensure_log_dir(self) -> bool:
        """Crea el directorio de log si no existe.

        Returns:
            True si el directorio existe o fue creado, False si falló.
        """
        try:
            self._log_dir.mkdir(parents=True, exist_ok=True)
            return True
        except OSError:
            return False

    def _get_os_user(self) -> str:
        """Obtiene el nombre del usuario del sistema operativo.

        Returns:
            Nombre del usuario actual del OS.
        """
        try:
            return os.getlogin()
        except OSError:
            return getpass.getuser()

    def _get_timestamp(self) -> str:
        """Genera timestamp ISO 8601 con timezone local.

        Returns:
            Timestamp en formato ISO 8601 con zona horaria.
        """
        local_tz = datetime.now(timezone.utc).astimezone().tzinfo
        now = datetime.now(tz=local_tz)
        return now.isoformat()

    def write_entry(self, entry: AuditLogEntry) -> bool:
        """Escribe una entrada de log en el archivo audit.jsonl.

        Si el campo os_user o timestamp están vacíos, los completa
        automáticamente con el usuario del OS y la hora actual.

        Args:
            entry: Entrada de auditoría a registrar.

        Returns:
            True si la escritura fue exitosa, False si falló.
            No lanza excepciones para no interrumpir el procesamiento.
        """
        try:
            if not self._ensure_log_dir():
                return False

            # Completar campos automáticos si están vacíos
            if not entry.os_user:
                entry = entry.model_copy(update={"os_user": self._get_os_user()})
            if not entry.timestamp:
                entry = entry.model_copy(
                    update={"timestamp": self._get_timestamp()}
                )

            line = entry.model_dump_json() + "\n"

            with open(self._log_file, "a", encoding="utf-8") as f:
                f.write(line)

            return True
        except (OSError, ValueError, TypeError):
            return False

    def read_entries(
        self, page: int = 1, page_size: int = 100
    ) -> list[AuditLogEntry]:
        """Lee entradas de log paginadas, de más reciente a más antigua.

        Args:
            page: Número de página (1-indexed).
            page_size: Cantidad de entradas por página (máximo 100).

        Returns:
            Lista de entradas de auditoría ordenadas de más reciente
            a más antigua. Lista vacía si no hay entradas o el archivo
            no existe.
        """
        # Validar parámetros
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 1
        if page_size > self.MAX_PAGE_SIZE:
            page_size = self.MAX_PAGE_SIZE

        if not self._log_file.exists():
            return []

        try:
            with open(self._log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except OSError:
            return []

        # Parsear todas las líneas válidas
        entries: list[AuditLogEntry] = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                entries.append(AuditLogEntry(**data))
            except (json.JSONDecodeError, ValueError, TypeError):
                # Saltar líneas corruptas
                continue

        # Ordenar de más reciente a más antiguo
        entries.reverse()

        # Aplicar paginación
        start = (page - 1) * page_size
        end = start + page_size

        return entries[start:end]
