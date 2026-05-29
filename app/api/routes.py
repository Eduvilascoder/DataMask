"""Rutas de la API REST para la aplicación de ofuscación de PDFs.

Incluye endpoints para:
- Validación de carpetas y listado de PDFs
- Configuración de tipos de datos sensibles
- Procesamiento de PDFs con progreso vía SSE
- Consulta de registros de auditoría
"""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.api.file_service import validate_and_list_documents
from app.config.service import ConfigService
from app.exceptions import ConfigError, PathValidationError
from app.log.service import LogService
from app.models import (
    AuditLogEntry,
    FileInfo,
    ProcessingResult,
    TypeConfig,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")

# --- Motor NER pre-cargado al inicio para evitar timeouts ---

_ner_engine = None


def _get_ner_engine():
    """Obtiene o crea la instancia singleton del NEREngine."""
    global _ner_engine
    if _ner_engine is None:
        from app.ner.engine import NEREngine
        base_dir = _get_base_dir()
        config_path = base_dir / "config" / "types_config.json"
        config_service = ConfigService(config_path=config_path)
        config = config_service.load()
        _ner_engine = NEREngine(config=config)
    return _ner_engine


# --- Estado global de procesamiento para SSE ---

_processing_state: dict = {
    "active": False,
    "total_files": 0,
    "processed_files": 0,
    "current_file": None,
    "results": [],
    "completed": False,
    "error": None,
}

_sse_events: asyncio.Queue = asyncio.Queue()


def _get_base_dir() -> Path:
    """Obtiene el directorio base del proyecto."""
    return Path(__file__).resolve().parent.parent.parent


# --- Request/Response Models ---


class FolderValidationRequest(BaseModel):
    """Request para validar una carpeta."""

    path: str


class FolderValidationResponse(BaseModel):
    """Response de validación de carpeta."""

    valid: bool
    files: list[FileInfo]
    error: str | None = None


class ProcessRequest(BaseModel):
    """Request para iniciar procesamiento."""

    folder_path: str
    selected_files: list[str] | None = None  # Lista de nombres de archivos seleccionados


class ProcessStartResponse(BaseModel):
    """Response al iniciar procesamiento."""

    message: str
    total_files: int


class LogsResponse(BaseModel):
    """Response de registros de auditoría."""

    entries: list[AuditLogEntry]
    page: int
    page_size: int
    total_in_page: int


# --- Endpoints de validación de carpeta (Task 8.1) ---


@router.post(
    "/folders/validate",
    response_model=FolderValidationResponse,
)
async def validate_folder(request: FolderValidationRequest) -> FolderValidationResponse:
    """Valida una ruta de carpeta y lista los archivos PDF encontrados.

    Returns:
        FolderValidationResponse con la lista de PDFs o error.

    Raises:
        HTTPException 422: Si la ruta no es válida.
    """
    try:
        files = validate_and_list_documents(request.path)
        return FolderValidationResponse(valid=True, files=files)
    except PathValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "code": exc.code,
                "message": exc.message,
            },
        ) from exc


# --- Endpoints de configuración (Task 8.1) ---


@router.get("/config")
async def get_config():
    """Retorna la configuración actual de tipos de datos sensibles."""
    base_dir = _get_base_dir()
    config_path = base_dir / "config" / "types_config.json"
    try:
        raw = config_path.read_text(encoding="utf-8")
        import json as json_mod
        data = json_mod.loads(raw)
        return data
    except Exception:
        # Return default config
        return {
            "version": 2,
            "types": {
                "nombre": {"enabled": True, "label": "NOMBRE", "description": "Detecta nombres y apellidos de personas"},
                "email": {"enabled": True, "label": "EMAIL", "description": "Detecta direcciones de correo electrónico"},
                "celular": {"enabled": True, "label": "CELULAR", "description": "Detecta números de celular con prefijo +54 9"},
                "telefono": {"enabled": True, "label": "TELEFONO", "description": "Detecta números de teléfono fijo con prefijo +54"},
                "direccion": {"enabled": True, "label": "DIRECCION", "description": "Detecta direcciones postales"},
                "tarjeta_credito": {"enabled": True, "label": "TARJETA_CREDITO", "description": "Detecta números de tarjeta de crédito (16 dígitos)"},
                "cuenta_bancaria": {"enabled": True, "label": "CUENTA_BANCARIA", "description": "Detecta números de CBU (22 dígitos)"},
                "dni": {"enabled": True, "label": "DNI", "description": "Detecta números de DNI argentino (7-8 dígitos)"},
                "cuit_cuil": {"enabled": True, "label": "CUIT_CUIL", "description": "Detecta números de CUIT/CUIL (XX-XXXXXXXX-X)"},
                "pasaporte": {"enabled": True, "label": "PASAPORTE", "description": "Detecta números de pasaporte argentino (AAX######)"},
            },
            "custom_types": [],
            "updated_at": None,
        }


@router.put("/config")
async def update_config(request: Request):
    """Actualiza la configuración de tipos de datos sensibles.

    Acepta el formato completo con descripciones editables y tipos custom.
    """
    import json as json_mod
    from datetime import datetime, timezone

    base_dir = _get_base_dir()
    config_path = base_dir / "config" / "types_config.json"

    data = await request.json()

    # Validar que al menos un tipo esté activo
    types = data.get("types", {})
    custom_types = data.get("custom_types", [])
    any_active = any(
        t.get("enabled", False) if isinstance(t, dict) else t
        for t in types.values()
    )
    any_custom_active = any(ct.get("enabled", False) for ct in custom_types)

    if not any_active and not any_custom_active:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "NO_ACTIVE_TYPE",
                "message": "Debe existir al menos 1 tipo activo para realizar el procesamiento.",
            },
        )

    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    data["version"] = 2

    try:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(
            json_mod.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    except OSError as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "WRITE_ERROR",
                "message": f"No se pudo guardar la configuración: {exc}",
            },
        )

    return data


# --- Endpoints de procesamiento con SSE (Task 8.2) ---


@router.post("/process", response_model=ProcessStartResponse)
async def start_processing(request: ProcessRequest) -> ProcessStartResponse:
    """Inicia el procesamiento de PDFs en la carpeta indicada.

    Valida la carpeta, lista los PDFs y lanza el procesamiento
    en background. El progreso se puede seguir vía SSE en
    GET /api/process/status.

    Raises:
        HTTPException 422: Si la carpeta no es válida o no hay PDFs.
        HTTPException 409: Si ya hay un procesamiento en curso.
    """
    global _processing_state, _sse_events

    if _processing_state["active"]:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "PROCESSING_ACTIVE",
                "message": "Ya hay un procesamiento en curso.",
            },
        )

    # Validar carpeta y listar documentos
    try:
        files = validate_and_list_documents(request.folder_path)
    except PathValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "code": exc.code,
                "message": exc.message,
            },
        ) from exc

    if not files:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "NO_PDF_FILES",
                "message": "No se encontraron documentos (PDF, Markdown o Word) en la carpeta indicada.",
            },
        )

    # Filtrar por archivos seleccionados si se especificaron
    if request.selected_files:
        selected_set = set(request.selected_files)
        files = [f for f in files if f.name in selected_set]
        if not files:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "NO_SELECTED_FILES",
                    "message": "Ninguno de los archivos seleccionados fue encontrado en la carpeta.",
                },
            )

    # Reiniciar estado y cola de eventos
    _sse_events = asyncio.Queue()
    _processing_state = {
        "active": True,
        "total_files": len(files),
        "processed_files": 0,
        "current_file": None,
        "results": [],
        "completed": False,
        "error": None,
    }

    # Lanzar procesamiento en background
    asyncio.create_task(_process_files(files, request.folder_path))

    return ProcessStartResponse(
        message="Procesamiento iniciado.",
        total_files=len(files),
    )


async def _process_files(files: list[FileInfo], folder_path: str) -> None:
    """Procesa los archivos PDF en background y emite eventos SSE.

    Args:
        files: Lista de archivos PDF a procesar.
        folder_path: Ruta de la carpeta origen.
    """
    global _processing_state

    base_dir = _get_base_dir()
    output_dir = str(base_dir / "ofuscados")
    log_base_path = str(base_dir)

    # Cargar configuración actual
    config_path = base_dir / "config" / "types_config.json"
    config_service = ConfigService(config_path=config_path)
    config = config_service.load()

    # Usar NEREngine pre-cargado y PDFProcessor
    try:
        from app.pdf.processor import PDFProcessor

        ner_engine = _get_ner_engine()
        # Actualizar config del motor NER con la configuración actual
        ner_engine.config = config
        processor = PDFProcessor(output_dir=output_dir, ner_engine=ner_engine)
    except (OSError, ImportError) as exc:
        error_msg = (
            f"No se pudo inicializar el motor NER: {exc}. "
            "Verifique que el modelo spaCy 'es_core_news_lg' esté instalado."
        )
        logger.error(error_msg)
        _processing_state["active"] = False
        _processing_state["completed"] = True
        _processing_state["error"] = error_msg
        await _sse_events.put({
            "event": "error",
            "data": {"message": error_msg},
        })
        await _sse_events.put({
            "event": "complete",
            "data": {
                "total": len(files),
                "success": 0,
                "failed": len(files),
                "error": error_msg,
            },
        })
        return

    log_service = LogService(base_path=log_base_path)
    results: list[ProcessingResult] = []
    success_count = 0
    failed_count = 0

    for i, file_info in enumerate(files):
        _processing_state["current_file"] = file_info.name
        _processing_state["processed_files"] = i

        # Emitir evento de inicio de archivo
        await _sse_events.put({
            "event": "file_start",
            "data": {
                "file": file_info.name,
                "index": i,
                "total": len(files),
            },
        })

        # Procesar archivo en un thread para no bloquear el event loop
        try:
            result = await asyncio.to_thread(
                processor.process_file, file_info.path
            )
        except Exception as exc:
            result = ProcessingResult(
                input_file=file_info.path,
                output_file="",
                success=False,
                entities_found=0,
                entities_by_type={},
                error=str(exc),
            )

        results.append(result)

        # Registrar en log de auditoría
        log_entry = AuditLogEntry(
            filename=file_info.name,
            file_size_bytes=file_info.size_bytes,
            os_user="",
            timestamp="",
            result="success" if result.success else "error",
            entities_detected=result.entities_found,
            entities_by_type=result.entities_by_type,
            error_detail=result.error,
        )
        log_service.write_entry(log_entry)

        if result.success:
            success_count += 1
            await _sse_events.put({
                "event": "file_complete",
                "data": {
                    "file": file_info.name,
                    "index": i,
                    "total": len(files),
                    "success": True,
                    "entities_found": result.entities_found,
                    "entities_by_type": result.entities_by_type,
                    "processing_time_ms": result.processing_time_ms,
                },
            })
        else:
            failed_count += 1
            await _sse_events.put({
                "event": "file_error",
                "data": {
                    "file": file_info.name,
                    "index": i,
                    "total": len(files),
                    "success": False,
                    "error": result.error,
                },
            })

    # Procesamiento completado
    _processing_state["active"] = False
    _processing_state["completed"] = True
    _processing_state["processed_files"] = len(files)
    _processing_state["results"] = [r.model_dump() for r in results]

    await _sse_events.put({
        "event": "complete",
        "data": {
            "total": len(files),
            "success": success_count,
            "failed": failed_count,
            "results": [r.model_dump() for r in results],
        },
    })


@router.get("/process/status")
async def process_status(request: Request) -> StreamingResponse:
    """Server-Sent Events stream para progreso de procesamiento.

    Emite eventos:
    - file_start: Inicio de procesamiento de un archivo
    - file_complete: Archivo procesado exitosamente
    - file_error: Error al procesar un archivo
    - error: Error fatal del procesamiento
    - complete: Procesamiento finalizado con resumen

    Returns:
        StreamingResponse con content-type text/event-stream.
    """
    return StreamingResponse(
        _event_generator(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


async def _event_generator(request: Request) -> AsyncGenerator[str, None]:
    """Genera eventos SSE desde la cola de procesamiento.

    Yields:
        Strings formateados como eventos SSE.
    """
    while True:
        # Verificar si el cliente se desconectó
        if await request.is_disconnected():
            break

        try:
            event = await asyncio.wait_for(_sse_events.get(), timeout=1.0)
            event_type = event.get("event", "message")
            data = json.dumps(event.get("data", {}), ensure_ascii=False)
            yield f"event: {event_type}\ndata: {data}\n\n"

            # Si es el evento final, terminar el stream
            if event_type in ("complete", "error"):
                break
        except asyncio.TimeoutError:
            # Enviar heartbeat para mantener la conexión
            yield ": heartbeat\n\n"


# --- Endpoint de logs (Task 8.3) ---


class BrowseRequest(BaseModel):
    """Request para navegar directorios."""
    path: str | None = None


class DirectoryEntry(BaseModel):
    """Entrada de directorio."""
    name: str
    path: str
    is_dir: bool


class BrowseResponse(BaseModel):
    """Response de navegación de directorios."""
    current_path: str
    parent_path: str | None
    entries: list[DirectoryEntry]


@router.post("/folders/browse", response_model=BrowseResponse)
async def browse_folders(request: BrowseRequest) -> BrowseResponse:
    """Navega directorios del sistema de archivos local.

    Si no se proporciona path, retorna el directorio home del usuario.
    Solo lista directorios (no archivos) para facilitar la selección.
    """
    import os

    if request.path:
        current = Path(request.path)
    else:
        current = Path.home()

    if not current.exists() or not current.is_dir():
        current = Path.home()

    entries: list[DirectoryEntry] = []
    try:
        for item in sorted(current.iterdir(), key=lambda p: p.name.lower()):
            # Solo mostrar directorios y archivos soportados
            if item.name.startswith("."):
                continue
            if item.is_dir():
                entries.append(DirectoryEntry(
                    name=item.name,
                    path=str(item),
                    is_dir=True,
                ))
            elif item.suffix.lower() in (".pdf", ".md", ".docx"):
                entries.append(DirectoryEntry(
                    name=item.name,
                    path=str(item),
                    is_dir=False,
                ))
    except PermissionError:
        pass

    parent = str(current.parent) if current.parent != current else None

    return BrowseResponse(
        current_path=str(current),
        parent_path=parent,
        entries=entries,
    )


@router.get("/logs", response_model=LogsResponse)
async def get_logs(
    page: int = Query(default=1, ge=1, description="Número de página"),
    page_size: int = Query(
        default=100, ge=1, le=100, description="Registros por página"
    ),
) -> LogsResponse:
    """Retorna registros de auditoría paginados.

    Los registros se ordenan de más reciente a más antiguo.

    Args:
        page: Número de página (default 1).
        page_size: Cantidad de registros por página (default 100, máximo 100).

    Returns:
        LogsResponse con las entradas y metadatos de paginación.
    """
    base_dir = _get_base_dir()
    log_service = LogService(base_path=str(base_dir))
    entries = log_service.read_entries(page=page, page_size=page_size)

    return LogsResponse(
        entries=entries,
        page=page,
        page_size=page_size,
        total_in_page=len(entries),
    )


# --- Endpoints de gestión de archivos ofuscados ---


class OutputFileInfo(BaseModel):
    """Info de un archivo ofuscado."""
    name: str
    size_bytes: int
    path: str
    folder: str  # "ofuscados" o "ofuscados_md"


class OutputFilesResponse(BaseModel):
    """Response con lista de archivos ofuscados."""
    files: list[OutputFileInfo]
    total: int


class DeleteRequest(BaseModel):
    """Request para borrar archivos."""
    files: list[str]  # nombres de archivos a borrar
    folder: str = "ofuscados"  # "ofuscados" o "ofuscados_md"


class DeleteResponse(BaseModel):
    """Response de borrado."""
    deleted: int
    errors: list[str]


@router.get("/output/files", response_model=OutputFilesResponse)
async def list_output_files(
    folder: str = Query(default="all", description="Carpeta: ofuscados, ofuscados_md, o all"),
) -> OutputFilesResponse:
    """Lista archivos en las carpetas de salida (ofuscados y/o ofuscados_md)."""
    base_dir = _get_base_dir()
    files: list[OutputFileInfo] = []

    folders_to_scan = []
    if folder in ("all", "ofuscados"):
        folders_to_scan.append(("ofuscados", base_dir / "ofuscados"))
    if folder in ("all", "ofuscados_md"):
        folders_to_scan.append(("ofuscados_md", base_dir / "ofuscados_md"))

    for folder_name, folder_path in folders_to_scan:
        if not folder_path.exists():
            continue
        for item in sorted(folder_path.iterdir(), key=lambda p: p.name.lower()):
            if item.is_file():
                try:
                    files.append(OutputFileInfo(
                        name=item.name,
                        size_bytes=item.stat().st_size,
                        path=str(item),
                        folder=folder_name,
                    ))
                except OSError:
                    continue

    return OutputFilesResponse(files=files, total=len(files))


@router.post("/output/delete", response_model=DeleteResponse)
async def delete_output_files(request: DeleteRequest) -> DeleteResponse:
    """Borra archivos de las carpetas de salida."""
    base_dir = _get_base_dir()
    folder_path = base_dir / request.folder

    if not folder_path.exists():
        raise HTTPException(
            status_code=404,
            detail={"code": "FOLDER_NOT_FOUND", "message": f"Carpeta '{request.folder}' no encontrada."},
        )

    deleted = 0
    errors: list[str] = []

    for filename in request.files:
        file_path = folder_path / filename
        # Security: ensure the file is within the expected folder
        try:
            file_path.resolve().relative_to(folder_path.resolve())
        except ValueError:
            errors.append(f"{filename}: ruta inválida")
            continue

        if not file_path.exists():
            errors.append(f"{filename}: no encontrado")
            continue

        try:
            file_path.unlink()
            deleted += 1
        except OSError as exc:
            errors.append(f"{filename}: {exc}")

    return DeleteResponse(deleted=deleted, errors=errors)


@router.post("/output/delete-all", response_model=DeleteResponse)
async def delete_all_output_files(
    folder: str = Query(default="ofuscados", description="Carpeta a vaciar"),
) -> DeleteResponse:
    """Borra todos los archivos de una carpeta de salida."""
    base_dir = _get_base_dir()
    folder_path = base_dir / folder

    if folder not in ("ofuscados", "ofuscados_md"):
        raise HTTPException(
            status_code=422,
            detail={"code": "INVALID_FOLDER", "message": "Solo se pueden vaciar 'ofuscados' u 'ofuscados_md'."},
        )

    if not folder_path.exists():
        return DeleteResponse(deleted=0, errors=[])

    deleted = 0
    errors: list[str] = []

    for item in folder_path.iterdir():
        if item.is_file():
            try:
                item.unlink()
                deleted += 1
            except OSError as exc:
                errors.append(f"{item.name}: {exc}")

    return DeleteResponse(deleted=deleted, errors=errors)


# --- Endpoints para ver contenido de archivos ofuscados ---


@router.get("/output/view/{folder}/{filename}")
async def view_output_file(folder: str, filename: str):
    """Sirve un archivo ofuscado para visualización.

    Para PDFs: retorna el archivo con content-type application/pdf.
    Para Markdown: retorna el contenido como texto.
    """
    from fastapi.responses import FileResponse, PlainTextResponse

    if folder not in ("ofuscados", "ofuscados_md"):
        raise HTTPException(
            status_code=422,
            detail={"code": "INVALID_FOLDER", "message": "Carpeta no válida."},
        )

    base_dir = _get_base_dir()
    file_path = base_dir / folder / filename

    # Security: ensure path is within expected folder
    try:
        file_path.resolve().relative_to((base_dir / folder).resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Acceso denegado.")

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(
            status_code=404,
            detail={"code": "NOT_FOUND", "message": f"Archivo '{filename}' no encontrado."},
        )

    if folder == "ofuscados_md":
        # Return markdown content as text
        content = file_path.read_text(encoding="utf-8")
        return PlainTextResponse(content, media_type="text/markdown; charset=utf-8")
    elif file_path.suffix.lower() == ".md":
        content = file_path.read_text(encoding="utf-8")
        return PlainTextResponse(content, media_type="text/markdown; charset=utf-8")
    elif file_path.suffix.lower() == ".docx":
        return FileResponse(
            str(file_path),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename=filename,
        )
    else:
        # Return PDF file
        return FileResponse(
            str(file_path),
            media_type="application/pdf",
            filename=filename,
        )


# --- Endpoints de documentación ---


class DocFileInfo(BaseModel):
    """Info de un archivo de documentación."""
    name: str
    title: str
    size_bytes: int


@router.get("/docs/list")
async def list_docs():
    """Lista los archivos de documentación disponibles."""
    base_dir = _get_base_dir()
    docs_dir = base_dir / "documentacion"

    if not docs_dir.exists():
        return {"files": []}

    # Mapeo de nombres a títulos legibles
    title_map = {
        "arquitectura.md": "Arquitectura del Sistema",
        "guia_usuario.md": "Guía de Usuario",
        "guia_instalacion.md": "Guía de Instalación",
        "flujo_aplicacion.md": "Flujo de la Aplicación",
        "security_assessment.md": "Assessment de Seguridad",
    }

    files = []
    for item in sorted(docs_dir.iterdir(), key=lambda p: p.name.lower()):
        if item.is_file() and item.suffix == ".md" and item.name != ".gitkeep":
            files.append(DocFileInfo(
                name=item.name,
                title=title_map.get(item.name, item.stem.replace("_", " ").title()),
                size_bytes=item.stat().st_size,
            ))

    return {"files": files}


@router.get("/docs/view/{filename}")
async def view_doc(filename: str):
    """Retorna el contenido de un archivo de documentación."""
    from fastapi.responses import PlainTextResponse

    base_dir = _get_base_dir()
    file_path = base_dir / "documentacion" / filename

    # Security check
    try:
        file_path.resolve().relative_to((base_dir / "documentacion").resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Acceso denegado.")

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail=f"Documento '{filename}' no encontrado.")

    content = file_path.read_text(encoding="utf-8")
    return {"name": filename, "content": content}
