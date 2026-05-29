"""Modelos de datos base de la aplicación."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class SensitiveDataType(str, Enum):
    """Tipos de datos sensibles detectables por el sistema."""

    NOMBRE = "NOMBRE"
    EMAIL = "EMAIL"
    CELULAR = "CELULAR"
    TELEFONO = "TELEFONO"
    DIRECCION = "DIRECCION"
    TARJETA_CREDITO = "TARJETA_CREDITO"
    CUENTA_BANCARIA = "CUENTA_BANCARIA"
    DNI = "DNI"
    CUIT_CUIL = "CUIT_CUIL"
    PASAPORTE = "PASAPORTE"


class TypeConfig(BaseModel):
    """Configuración de tipos de datos sensibles a detectar.

    Cada campo booleano indica si el tipo correspondiente
    está activo para detección.
    """

    nombre: bool = True
    email: bool = True
    celular: bool = True
    telefono: bool = True
    direccion: bool = True
    tarjeta_credito: bool = True
    cuenta_bancaria: bool = True
    dni: bool = True
    cuit_cuil: bool = True
    pasaporte: bool = True


class FileInfo(BaseModel):
    """Información básica de un archivo PDF encontrado."""

    name: str
    size_bytes: int
    path: str


class DetectedEntity(BaseModel):
    """Entidad sensible detectada en el texto de un PDF."""

    text: str
    entity_type: SensitiveDataType
    start: int
    end: int
    confidence: float = Field(ge=0.0, le=1.0)
    page: int


class ProcessingResult(BaseModel):
    """Resultado del procesamiento de un archivo PDF."""

    input_file: str
    output_file: str
    success: bool
    entities_found: int
    entities_by_type: dict[str, int] = Field(default_factory=dict)
    error: str | None = None
    processing_time_ms: int = 0


class AuditLogEntry(BaseModel):
    """Entrada del registro de auditoría."""

    filename: str
    file_size_bytes: int
    os_user: str
    timestamp: str  # ISO 8601 con timezone
    result: str  # "success" | "error"
    entities_detected: int
    entities_by_type: dict[str, int] = Field(default_factory=dict)
    error_detail: str | None = None
