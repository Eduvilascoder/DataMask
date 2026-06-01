@echo off
REM =============================================================================
REM run.bat - Iniciar la aplicación en Windows
REM Aplicación de Ofuscación de Datos Sensibles en PDFs
REM =============================================================================

setlocal

REM Directorio base del proyecto
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM Puerto por defecto
if "%PORT%"=="" set PORT=3000
if "%HOST%"=="" set HOST=127.0.0.1

echo.
echo ============================================================
echo   Ofuscacion de Datos Sensibles en PDFs
echo ============================================================
echo.

REM Verificar que el entorno virtual existe
if not exist "venv\" (
    echo [ERROR] Entorno virtual no encontrado.
    echo   Ejecute primero el instalador:
    echo     setup.bat
    exit /b 1
)

REM Activar entorno virtual
call venv\Scripts\activate.bat

REM Verificar que uvicorn está disponible
where uvicorn >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] uvicorn no encontrado en el entorno virtual.
    echo   Ejecute el instalador para instalar las dependencias:
    echo     setup.bat
    exit /b 1
)

REM Crear carpetas necesarias si no existen
if not exist "log\" mkdir log
if not exist "ofuscados\" mkdir ofuscados
if not exist "ofuscados_md\" mkdir ofuscados_md
if not exist "test\" mkdir test
if not exist "documentacion\" mkdir documentacion
if not exist "models\" mkdir models
if not exist "config\" mkdir config

REM Iniciar Ollama en background si está disponible
where ollama >nul 2>&1
if %errorlevel% equ 0 (
    curl -s http://localhost:11434/api/tags >nul 2>&1
    if %errorlevel% neq 0 (
        echo [OK] Iniciando Ollama en background...
        start /b ollama serve >nul 2>&1
        timeout /t 3 /nobreak >nul
    )
    echo [OK] Ollama activo ^(Llama 3.1 8B^)
) else (
    echo [INFO] Ollama no instalado - usando spaCy como fallback
)
if not exist "test\" mkdir test
if not exist "documentacion\" mkdir documentacion
if not exist "models\" mkdir models
if not exist "config\" mkdir config

echo [OK] Iniciando servidor en http://localhost:%PORT%
echo [OK] Presione Ctrl+C para detener el servidor
echo.

REM Iniciar uvicorn
uvicorn app.main:app --host %HOST% --port %PORT%

endlocal
