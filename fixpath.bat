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

set "SCRIPT_DIR=%~dp0"
set "FIXES=0"

REM =============================================================================
REM Buscar Ollama
REM =============================================================================

echo [INFO] Buscando Ollama...
set "OLLAMA_DIR="
if exist "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" set "OLLAMA_DIR=%LOCALAPPDATA%\Programs\Ollama"
if exist "%ProgramFiles%\Ollama\ollama.exe" set "OLLAMA_DIR=%ProgramFiles%\Ollama"
if exist "%USERPROFILE%\AppData\Local\Ollama\ollama.exe" set "OLLAMA_DIR=%USERPROFILE%\AppData\Local\Ollama"

if not "!OLLAMA_DIR!"=="" (
    echo [OK] Ollama encontrado en: !OLLAMA_DIR!
    echo [FIX] Agregando al PATH del usuario via PowerShell...
    powershell -Command "$p = [Environment]::GetEnvironmentVariable('Path','User'); if ($p -notlike '*Ollama*') { [Environment]::SetEnvironmentVariable('Path', $p + ';!OLLAMA_DIR!', 'User'); Write-Host 'Agregado' } else { Write-Host 'Ya estaba' }"
    set "PATH=!PATH!;!OLLAMA_DIR!"
    set /a FIXES+=1
) else (
    echo [AVISO] Ollama no encontrado. Instale desde: https://ollama.com/download
)

REM =============================================================================
REM Buscar Node.js
REM =============================================================================

echo [INFO] Buscando Node.js...
set "NODE_DIR="
if exist "%SCRIPT_DIR%node\node.exe" set "NODE_DIR=%SCRIPT_DIR%node"
if exist "C:\Program Files\nodejs\node.exe" set "NODE_DIR=C:\Program Files\nodejs"

if not "!NODE_DIR!"=="" (
    echo [OK] Node.js encontrado en: !NODE_DIR!
    echo [FIX] Agregando al PATH del usuario via PowerShell...
    powershell -Command "$p = [Environment]::GetEnvironmentVariable('Path','User'); if ($p -notlike '*nodejs*' -and $p -notlike '*\node*') { [Environment]::SetEnvironmentVariable('Path', $p + ';!NODE_DIR!', 'User'); Write-Host 'Agregado' } else { Write-Host 'Ya estaba' }"
    set "PATH=!PATH!;!NODE_DIR!"
    set /a FIXES+=1
) else (
    echo [AVISO] Node.js no encontrado. Ejecute setup.bat para instalarlo.
)

REM =============================================================================
REM Buscar Python
REM =============================================================================

echo [INFO] Buscando Python...
set "PY_DIR="
for %%P in (
    "%LOCALAPPDATA%\Programs\Python\Python313"
    "%LOCALAPPDATA%\Programs\Python\Python312"
    "%LOCALAPPDATA%\Programs\Python\Python311"
    "%LOCALAPPDATA%\Programs\Python\Python310"
    "%LOCALAPPDATA%\Programs\Python\Python39"
) do (
    if "!PY_DIR!"=="" (
        if exist "%%~P\python.exe" set "PY_DIR=%%~P"
    )
)

if not "!PY_DIR!"=="" (
    echo [OK] Python encontrado en: !PY_DIR!
    echo [FIX] Agregando al PATH del usuario via PowerShell...
    powershell -Command "$p = [Environment]::GetEnvironmentVariable('Path','User'); if ($p -notlike '*Python3*') { [Environment]::SetEnvironmentVariable('Path', $p + ';!PY_DIR!;!PY_DIR!\Scripts', 'User'); Write-Host 'Agregado' } else { Write-Host 'Ya estaba' }"
    set "PATH=!PATH!;!PY_DIR!;!PY_DIR!\Scripts"
    set /a FIXES+=1
) else (
    echo [AVISO] Python no encontrado.
)

REM =============================================================================
REM Verificacion final
REM =============================================================================

echo.
echo ============================================================
echo   Verificacion:
echo ============================================================
echo.

ollama --version 2>nul && echo [OK] Ollama funciona || echo [X] Ollama no responde
node --version 2>nul && echo [OK] Node.js funciona || echo [X] Node.js no responde
python --version 2>nul && echo [OK] Python funciona || echo [X] Python no responde (puede ser alias MS Store)

echo.
echo ============================================================
echo   Listo. Si algo no funciona en ESTA terminal,
echo   cierre y abra una nueva terminal.
echo   run.bat funciona sin importar el PATH del sistema.
echo ============================================================
echo.

endlocal
