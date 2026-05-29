"""Servicio de validación de rutas y listado de documentos.

Provee funcionalidad para:
- Validar rutas del sistema de archivos (existencia, tipo, permisos)
- Detectar límites de longitud de ruta según el OS
- Listar archivos PDF, Markdown y Word (case-insensitive) en una carpeta
- Manejar rutas con espacios, caracteres acentuados y separadores nativos
"""

from __future__ import annotations

import os
import platform
from pathlib import Path

from app.exceptions import PathValidationError
from app.models import FileInfo


# Límites de longitud de ruta por sistema operativo
_MAX_PATH_WINDOWS = 260
_MAX_PATH_MACOS = 1024
_MAX_PATH_LINUX = 4096

# Extensiones soportadas para comparación case-insensitive
_SUPPORTED_EXTENSIONS: set[str] = {".pdf", ".md", ".docx"}


def _get_max_path_length() -> int:
    """Retorna el límite máximo de longitud de ruta según el OS actual.

    Returns:
        Límite en caracteres: 260 para Windows, 1024 para macOS, 4096 para Linux.
    """
    system = platform.system().lower()
    if system == "windows":
        return _MAX_PATH_WINDOWS
    if system == "darwin":
        return _MAX_PATH_MACOS
    return _MAX_PATH_LINUX


def _get_os_name() -> str:
    """Retorna el nombre del sistema operativo para mensajes de error.

    Returns:
        Nombre legible del OS: 'Windows', 'macOS' o 'Linux'.
    """
    system = platform.system().lower()
    if system == "windows":
        return "Windows"
    if system == "darwin":
        return "macOS"
    return "Linux"


def validate_path(path_str: str) -> Path:
    """Valida una ruta del sistema de archivos.

    Verifica:
    1. Longitud de ruta dentro del límite del OS
    2. Existencia de la ruta
    3. Que la ruta sea un directorio
    4. Permisos de lectura sobre el directorio

    Args:
        path_str: Ruta como cadena de texto. Puede contener espacios,
                  caracteres acentuados y separadores nativos del OS.

    Returns:
        Objeto Path validado y resuelto.

    Raises:
        PathValidationError: Con código específico según la causa:
            - PATH_TOO_LONG: La ruta excede el límite del OS.
            - NOT_FOUND: La ruta no existe.
            - NOT_DIR: La ruta existe pero no es un directorio.
            - NO_PERMISSION: Sin permisos de lectura.
    """
    max_length = _get_max_path_length()
    os_name = _get_os_name()

    # Validar longitud de ruta
    if len(path_str) > max_length:
        raise PathValidationError(
            code="PATH_TOO_LONG",
            message=(
                f"La ruta excede el límite de {max_length} caracteres "
                f"permitido por {os_name}."
            ),
            recoverable=True,
        )

    # Normalizar la ruta usando Path (maneja separadores nativos del OS)
    path = Path(path_str)

    # Validar existencia
    if not path.exists():
        raise PathValidationError(
            code="NOT_FOUND",
            message=f"La ruta no existe: {path_str}",
            recoverable=True,
        )

    # Validar que sea un directorio
    if not path.is_dir():
        raise PathValidationError(
            code="NOT_DIR",
            message=f"La ruta no es un directorio: {path_str}",
            recoverable=True,
        )

    # Validar permisos de lectura
    if not os.access(path, os.R_OK):
        raise PathValidationError(
            code="NO_PERMISSION",
            message=(
                f"Sin permisos de lectura sobre el directorio: {path_str}"
            ),
            recoverable=True,
        )

    return path


def list_document_files(directory: Path) -> list[FileInfo]:
    """Lista archivos de documento en el nivel superior de un directorio.

    Busca archivos con extensión `.pdf`, `.md` o `.docx` de forma
    case-insensitive. Solo lista archivos en el nivel superior,
    sin recursión en subdirectorios.

    Maneja correctamente rutas con:
    - Espacios en nombres de archivo
    - Caracteres acentuados (á, é, í, ó, ú, ñ)
    - Separadores de ruta nativos del OS

    Args:
        directory: Objeto Path del directorio ya validado.

    Returns:
        Lista de FileInfo con nombre, tamaño en bytes y ruta completa
        de cada documento encontrado. Lista vacía si no hay documentos.
    """
    doc_files: list[FileInfo] = []

    try:
        for entry in directory.iterdir():
            # Solo archivos (no directorios ni symlinks a directorios)
            if not entry.is_file():
                continue

            # Comparación case-insensitive de la extensión
            if entry.suffix.lower() not in _SUPPORTED_EXTENSIONS:
                continue

            # Obtener tamaño del archivo
            try:
                size = entry.stat().st_size
            except OSError:
                # Si no se puede obtener el tamaño, omitir el archivo
                continue

            doc_files.append(
                FileInfo(
                    name=entry.name,
                    size_bytes=size,
                    path=str(entry),
                )
            )
    except PermissionError:
        raise PathValidationError(
            code="NO_PERMISSION",
            message=(
                f"Sin permisos de lectura sobre el directorio: {directory}"
            ),
            recoverable=True,
        )

    # Ordenar por nombre para resultados consistentes
    doc_files.sort(key=lambda f: f.name.lower())

    return doc_files


def validate_and_list_documents(path_str: str) -> list[FileInfo]:
    """Valida una ruta y lista los documentos encontrados.

    Función de conveniencia que combina validación de ruta con
    listado de archivos soportados (PDF, Markdown, Word).
    Es el punto de entrada principal para el endpoint de validación
    de carpetas.

    Args:
        path_str: Ruta de la carpeta a validar y explorar.

    Returns:
        Lista de FileInfo con los documentos encontrados.

    Raises:
        PathValidationError: Si la ruta no es válida (ver validate_path).
    """
    directory = validate_path(path_str)
    return list_document_files(directory)


# Alias de compatibilidad
validate_and_list_pdfs = validate_and_list_documents
list_pdf_files = list_document_files
