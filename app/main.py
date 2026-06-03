"""Entry point de la aplicación FastAPI para ofuscación de datos sensibles en PDFs."""

import os
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router as api_router

# Directorio raíz del proyecto (un nivel arriba de app/)
BASE_DIR = Path(__file__).resolve().parent.parent

# Puerto por defecto
DEFAULT_PORT = 3000

# Carpetas que deben existir al iniciar la aplicación
REQUIRED_DIRS: list[str] = [
    "log",
    "ofuscados",
    "ofuscados_md",
    "test",
    "documentacion",
    "models",
    "config",
]


def _create_required_directories() -> None:
    """Crea las carpetas requeridas si no existen."""
    for dir_name in REQUIRED_DIRS:
        dir_path = BASE_DIR / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)


def _resolve_frontend_dir() -> Path | None:
    """Resuelve el directorio del build del frontend.

    Vite por defecto genera en dist/, pero el proyecto puede
    configurar outDir a build/. Se busca en ambas ubicaciones,
    priorizando dist/ (default de Vite).

    Returns:
        Path al directorio del build si existe, None en caso contrario.
    """
    candidates = [
        BASE_DIR / "frontend" / "dist",
        BASE_DIR / "frontend" / "build",
    ]
    for candidate in candidates:
        if candidate.is_dir() and (candidate / "index.html").is_file():
            return candidate
    return None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Evento de ciclo de vida: crea carpetas faltantes al iniciar."""
    _create_required_directories()

    port = os.environ.get("PORT", str(DEFAULT_PORT))
    print(f"\n{'=' * 50}")
    print(f"  DataMask - Servidor iniciado")
    print(f"  Enmascarar datos sensibles")
    print(f"  v3.1 - by EduTheCoder")
    print(f"")
    print(f"  Accede a la aplicación en:")
    print(f"  http://localhost:{port}")
    print(f"{'=' * 50}\n")

    yield


app = FastAPI(
    title="PDF Datos Sensibles",
    description="Aplicación local para ofuscación de datos sensibles en PDFs",
    version="3.1.0",
    lifespan=lifespan,
)

# Middleware CORS para desarrollo (mismo origen en producción).
# En producción, el frontend se sirve desde el mismo origen que la API,
# eliminando la necesidad de CORS. Estas reglas solo aplican durante
# desarrollo local con Vite dev server.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Registrar rutas de la API (antes del mount de estáticos)
app.include_router(api_router)


@app.get("/api/health")
async def health_check() -> JSONResponse:
    """Health check del servidor."""
    return JSONResponse(
        content={"status": "ok", "service": "pdf-datos-sensibles"},
        status_code=200,
    )


# Servir archivos estáticos del build de React (si existe).
# Se monta al FINAL para que las rutas /api/* tengan prioridad.
# html=True permite que el SPA routing funcione: cualquier ruta
# que no sea un archivo estático ni una ruta API sirve index.html.
_frontend_dir = _resolve_frontend_dir()
if _frontend_dir is not None:
    # Montar assets estáticos (JS, CSS, imágenes)
    _assets_dir = _frontend_dir / "assets"
    if _assets_dir.is_dir():
        app.mount(
            "/assets",
            StaticFiles(directory=str(_assets_dir)),
            name="frontend-assets",
        )

    # Catch-all para SPA routing: cualquier ruta que no sea /api/*
    # ni un asset estático sirve index.html para que React Router
    # maneje la navegación del lado del cliente.
    @app.get("/{full_path:path}")
    async def serve_spa(request: Request, full_path: str) -> FileResponse:
        """Sirve index.html para todas las rutas del SPA."""
        # Intentar servir archivo estático si existe
        file_path = _frontend_dir / full_path
        if full_path and file_path.is_file():
            return FileResponse(str(file_path))
        # Fallback a index.html para SPA routing
        return FileResponse(str(_frontend_dir / "index.html"))
