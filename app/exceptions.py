"""Jerarquía de excepciones de la aplicación."""


class AppError(Exception):
    """Error base de la aplicación.

    Attributes:
        code: Código identificador del error.
        message: Mensaje descriptivo del error.
        recoverable: Indica si la aplicación puede continuar operando.
    """

    def __init__(
        self, code: str, message: str, recoverable: bool = True
    ) -> None:
        self.code = code
        self.message = message
        self.recoverable = recoverable
        super().__init__(message)


class PathValidationError(AppError):
    """Errores de validación de rutas del sistema de archivos.

    Códigos comunes:
        - NOT_FOUND: La ruta no existe.
        - NOT_DIR: La ruta existe pero no es un directorio.
        - NO_PERMISSION: Sin permisos de lectura.
        - PATH_TOO_LONG: La ruta excede el límite del OS.
    """

    pass


class PDFProcessingError(AppError):
    """Errores durante el procesamiento de archivos PDF.

    Códigos comunes:
        - CORRUPTED: El PDF está corrupto o no es válido.
        - PASSWORD_PROTECTED: El PDF requiere contraseña.
        - WRITE_ERROR: Error al escribir el archivo de salida.
        - EXTRACTION_ERROR: Error al extraer texto del PDF.
    """

    pass


class ConfigError(AppError):
    """Errores de configuración de la aplicación.

    Códigos comunes:
        - INVALID_JSON: El archivo de configuración no es JSON válido.
        - MISSING_FIELDS: Faltan campos requeridos.
        - NO_ACTIVE_TYPE: Ningún tipo de dato sensible está activo.
        - WRITE_ERROR: Error al persistir la configuración.
    """

    pass
