@echo off
REM =============================================================================
REM stop.bat - Detener la aplicación DataMask en Windows
REM =============================================================================

echo.
echo ============================================================
echo   DataMask - Deteniendo servidor
echo ============================================================
echo.

REM Buscar procesos uvicorn
set "FOUND=0"
for /f "tokens=2" %%a in ('tasklist /fi "imagename eq python.exe" /fo list 2^>nul ^| findstr /i "PID"') do (
    set "FOUND=1"
)

REM Intentar matar procesos uvicorn por nombre de ventana o línea de comando
taskkill /f /fi "WINDOWTITLE eq *uvicorn*" >nul 2>&1
taskkill /f /im "uvicorn.exe" >nul 2>&1

REM Buscar python ejecutando uvicorn
for /f "tokens=2 delims=," %%a in ('wmic process where "commandline like '%%uvicorn app.main:app%%'" get processid /format:csv 2^>nul ^| findstr /r "[0-9]"') do (
    echo [OK] Deteniendo proceso PID: %%a
    taskkill /f /pid %%a >nul 2>&1
    set "FOUND=1"
)

if "%FOUND%"=="0" (
    echo [INFO] No se encontro ningun proceso de DataMask en ejecucion.
) else (
    echo.
    echo [OK] DataMask detenido correctamente.
)

echo.
