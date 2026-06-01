@echo off
REM =============================================================================
REM fixpath.bat - Corrige problemas de PATH para instalaciones existentes
REM DataMask v2.0
REM =============================================================================

setlocal enabledelayedexpansion

echo.
echo ============================================================
echo   DataMask - Correccion de PATH
echo ============================================================
echo.
echo   Este script agrega al PATH del sistema las rutas de:
echo   - Python (si esta instalado pero no en PATH)
echo   - Node.js (portable en carpeta node\)
echo   - Ollama (si esta instalado pero no en PATH)
echo.

set "SCRIPT_DIR=%~dp0"
set "FIXES_APPLIED=0"

REM =============================================================================
REM Buscar y agregar Python al PATH
REM =============================================================================

echo [INFO] Verificando Python...
where python >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Python ya esta en el PATH.
) else (
    set "PY_PATH="
    for %%P in (
        "%LOCALAPPDATA%\Programs\Python\Python313"
        "%LOCALAPPDATA%\Programs\Python\Python312"
        "%LOCALAPPDATA%\Programs\Python\Python311"
        "%LOCALAPPDATA%\Programs\Python\Python310"
        "%LOCALAPPDATA%\Programs\Python\Python39"
        "C:\Python312"
        "C:\Python311"
        "%ProgramFiles%\Python312"
        "%ProgramFiles%\Python311"
    ) do (
        if "!PY_PATH!"=="" (
            if exist "%%~P\python.exe" set "PY_PATH=%%~P"
        )
    )
    if not "!PY_PATH!"=="" (
        echo [FIX] Python encontrado en: !PY_PATH!
        echo [FIX] Agregando al PATH del usuario...
        setx PATH "%PATH%;!PY_PATH!;!PY_PATH!\Scripts" >nul 2>&1
        set "PATH=!PATH!;!PY_PATH!;!PY_PATH!\Scripts"
        set /a FIXES_APPLIED+=1
        echo [OK] Python agregado al PATH.
    ) else (
        echo [AVISO] Python no encontrado. Instale desde: https://www.python.org/downloads/
    )
)

REM =============================================================================
REM Buscar y agregar Node.js al PATH
REM =============================================================================

echo [INFO] Verificando Node.js...
where node >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Node.js ya esta en el PATH.
) else (
    if exist "%SCRIPT_DIR%node\node.exe" (
        echo [FIX] Node.js portable encontrado en: %SCRIPT_DIR%node\
        echo [FIX] Agregando al PATH del usuario...
        setx PATH "%PATH%;%SCRIPT_DIR%node" >nul 2>&1
        set "PATH=!PATH!;%SCRIPT_DIR%node"
        set /a FIXES_APPLIED+=1
        echo [OK] Node.js agregado al PATH.
    ) else if exist "C:\Program Files\nodejs\node.exe" (
        echo [FIX] Node.js encontrado en: C:\Program Files\nodejs\
        echo [FIX] Agregando al PATH del usuario...
        setx PATH "%PATH%;C:\Program Files\nodejs" >nul 2>&1
        set "PATH=!PATH!;C:\Program Files\nodejs"
        set /a FIXES_APPLIED+=1
        echo [OK] Node.js agregado al PATH.
    ) else (
        echo [AVISO] Node.js no encontrado. Ejecute setup.bat para instalarlo.
    )
)

REM =============================================================================
REM Buscar y agregar Ollama al PATH
REM =============================================================================

echo [INFO] Verificando Ollama...
where ollama >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Ollama ya esta en el PATH.
) else (
    set "OLLAMA_PATH="
    if exist "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" set "OLLAMA_PATH=%LOCALAPPDATA%\Programs\Ollama"
    if exist "%ProgramFiles%\Ollama\ollama.exe" set "OLLAMA_PATH=%ProgramFiles%\Ollama"
    if exist "%USERPROFILE%\AppData\Local\Ollama\ollama.exe" set "OLLAMA_PATH=%USERPROFILE%\AppData\Local\Ollama"

    if not "!OLLAMA_PATH!"=="" (
        echo [FIX] Ollama encontrado en: !OLLAMA_PATH!
        echo [FIX] Agregando al PATH del usuario...
        setx PATH "%PATH%;!OLLAMA_PATH!" >nul 2>&1
        set "PATH=!PATH!;!OLLAMA_PATH!"
        set /a FIXES_APPLIED+=1
        echo [OK] Ollama agregado al PATH.
    ) else (
        echo [AVISO] Ollama no encontrado. Instale desde: https://ollama.com/download
    )
)

REM =============================================================================
REM Desactivar alias de Microsoft Store para Python
REM =============================================================================

echo [INFO] Verificando alias de Microsoft Store...
if exist "%LOCALAPPDATA%\Microsoft\WindowsApps\python.exe" (
    echo [AVISO] Alias de Microsoft Store detectado para Python.
    echo   Para desactivarlo manualmente:
    echo     Configuracion ^> Aplicaciones ^> Alias de ejecucion
    echo     Desactive "python.exe" y "python3.exe"
)

REM =============================================================================
REM Resumen
REM =============================================================================

echo.
echo ============================================================
if !FIXES_APPLIED! gtr 0 (
    echo   Se aplicaron !FIXES_APPLIED! correcciones al PATH.
    echo   Los cambios son permanentes para nuevas terminales.
    echo.
    echo   Para usar los cambios en ESTA terminal, cierre y abra
    echo   una nueva, o ejecute run.bat directamente ^(ya funciona^).
) else (
    echo   No se necesitaron correcciones. Todo esta en el PATH.
)
echo ============================================================
echo.

endlocal
