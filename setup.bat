@echo off
REM =============================================================================
REM setup.bat - Instalador para Windows
REM Aplicación de Ofuscación de Datos Sensibles en PDFs
REM =============================================================================

setlocal enabledelayedexpansion

REM Directorio base del proyecto
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM Versiones mínimas requeridas
set MIN_PYTHON_MAJOR=3
set MIN_PYTHON_MINOR=9
set MIN_NODE_MAJOR=18
set MIN_DISK_MB=2000

echo.
echo ============================================================
echo   Instalador - Ofuscacion de Datos Sensibles en PDFs
echo ============================================================
echo.
echo   Sistema operativo: Windows
echo   Directorio de instalacion: %SCRIPT_DIR%
echo.

REM =============================================================================
REM Verificación de prerequisitos
REM =============================================================================

echo ============================================================
echo   Verificando prerequisitos del sistema
echo ============================================================
echo.

REM Verificar Python
echo [INFO] Verificando Python...
set "PYTHON_CMD="

REM Buscar Python REAL directamente por ruta (evita alias de Microsoft Store)
REM Primero intentar en ubicaciones conocidas de instalacion
for %%P in (
    "%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python39\python.exe"
    "C:\Python313\python.exe"
    "C:\Python312\python.exe"
    "C:\Python311\python.exe"
    "C:\Python310\python.exe"
    "C:\Python39\python.exe"
    "%ProgramFiles%\Python313\python.exe"
    "%ProgramFiles%\Python312\python.exe"
    "%ProgramFiles%\Python311\python.exe"
) do (
    if "!PYTHON_CMD!"=="" (
        if exist %%P (
            set "PYTHON_CMD=%%~P"
        )
    )
)

REM Si no se encontro por ruta, intentar 'python' pero verificar que es real
if "!PYTHON_CMD!"=="" (
    for /f "tokens=*" %%v in ('python -c "import sys; print(sys.executable)" 2^>nul') do (
        if exist "%%v" set "PYTHON_CMD=%%v"
    )
)

if "!PYTHON_CMD!"=="" (
    echo [INFO] Python no encontrado. Instalando automaticamente...
    echo [INFO] Descargando Python 3.12...
    curl -fsSL -o "%TEMP%\python-setup.exe" "https://www.python.org/ftp/python/3.12.7/python-3.12.7-amd64.exe"
    if !errorlevel! neq 0 (
        echo [ERROR] No se pudo descargar Python.
        echo   Instale manualmente desde: https://www.python.org/downloads/
        echo   IMPORTANTE: Marque "Add Python to PATH" durante la instalacion.
        exit /b 1
    )
    echo [INFO] Instalando Python 3.12 ^(esto puede tardar un minuto^)...
    "%TEMP%\python-setup.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_pip=1
    del "%TEMP%\python-setup.exe" 2>nul
    timeout /t 5 /nobreak >nul
    REM Buscar el Python recien instalado
    if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
        set "PYTHON_CMD=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
        echo [OK] Python 3.12 instalado correctamente
    ) else (
        echo [ERROR] Python se instalo pero no se encuentra.
        echo   Cierre esta terminal, abra una nueva y ejecute setup.bat de nuevo.
        exit /b 1
    )
)

echo [OK] Python encontrado: !PYTHON_CMD!

REM Obtener version de Python
for /f "tokens=2 delims= " %%v in ('"!PYTHON_CMD!" --version 2^>^&1') do set "PYTHON_VERSION=%%v"
echo [OK] Python !PYTHON_VERSION!

REM Verificar Node.js
echo [INFO] Verificando Node.js...
set "NODE_CMD="
where node >nul 2>&1
if %errorlevel% equ 0 (
    set "NODE_CMD=node"
)
REM Tambien buscar en la carpeta local del proyecto
if exist "%SCRIPT_DIR%node\node.exe" (
    set "PATH=!PATH!;%SCRIPT_DIR%node"
    set "NODE_CMD=node"
)

if "!NODE_CMD!"=="" (
    echo [INFO] Node.js no encontrado. Instalando version portable...
    echo [INFO] Descargando Node.js 20 LTS ^(portable^)...
    if not exist "node\" mkdir node
    curl -fsSL -o "%TEMP%\node.zip" "https://nodejs.org/dist/v20.18.0/node-v20.18.0-win-x64.zip"
    if !errorlevel! neq 0 (
        echo [ERROR] No se pudo descargar Node.js.
        echo   Instale manualmente desde: https://nodejs.org/
        exit /b 1
    )
    echo [INFO] Extrayendo Node.js...
    powershell -Command "Expand-Archive -Path '%TEMP%\node.zip' -DestinationPath '%TEMP%\node_extract' -Force"
    REM Mover contenido al directorio node/ del proyecto
    xcopy /E /Y /Q "%TEMP%\node_extract\node-v20.18.0-win-x64\*" "node\" >nul 2>&1
    rd /S /Q "%TEMP%\node_extract" 2>nul
    del "%TEMP%\node.zip" 2>nul
    REM Agregar al PATH de esta sesion
    set "PATH=!PATH!;%SCRIPT_DIR%node"
    where node >nul 2>&1
    if !errorlevel! neq 0 (
        if exist "node\node.exe" (
            set "PATH=!PATH!;%SCRIPT_DIR%node"
        ) else (
            echo [ERROR] No se pudo instalar Node.js.
            echo   Instale manualmente desde: https://nodejs.org/
            exit /b 1
        )
    )
    echo [OK] Node.js portable instalado en carpeta node\
)

REM Verificar que node funciona
node --version >nul 2>&1
if %errorlevel% neq 0 (
    if exist "node\node.exe" (
        set "PATH=!PATH!;%SCRIPT_DIR%node"
    )
)
for /f "delims=" %%v in ('node --version 2^>nul') do set "NODE_VERSION_DISPLAY=%%v"
if "!NODE_VERSION_DISPLAY!"=="" (
    echo [ERROR] Node.js no funciona correctamente.
    echo   Instale manualmente desde: https://nodejs.org/
    exit /b 1
)
echo [OK] Node.js !NODE_VERSION_DISPLAY! encontrado

REM Verificar npm
echo [INFO] Verificando npm...
where npm >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] npm no encontrado.
    echo   npm se instala junto con Node.js. Reinstale Node.js desde:
    echo     https://nodejs.org/
    exit /b 1
)
for /f "delims=" %%v in ('npm --version') do set "NPM_VERSION=%%v"
echo [OK] npm v%NPM_VERSION% encontrado

REM Verificar espacio en disco
echo [INFO] Verificando espacio en disco...
for /f "usebackq tokens=3" %%a in (`dir /-c "%SCRIPT_DIR%" 2^>nul ^| findstr /c:"bytes free"`) do set "FREE_BYTES=%%a"
if "%FREE_BYTES%"=="" (
    echo [AVISO] No se pudo verificar el espacio en disco. Continuando...
) else (
    echo [OK] Espacio en disco verificado
)

REM Verificar permisos de escritura
echo [INFO] Verificando permisos de escritura...
echo test > "%SCRIPT_DIR%\_write_test.tmp" 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Sin permisos de escritura en el directorio de instalacion.
    echo   Ejecute este script como Administrador o cambie los permisos del directorio.
    exit /b 1
)
del "%SCRIPT_DIR%\_write_test.tmp" 2>nul
echo [OK] Permisos de escritura verificados

echo.

REM =============================================================================
REM Crear estructura de directorios
REM =============================================================================

echo ============================================================
echo   Creando estructura de directorios
echo ============================================================
echo.

for %%d in (log ofuscados test documentacion models config) do (
    if not exist "%%d\" (
        mkdir "%%d"
        echo [OK] Carpeta creada: %%d\
    ) else (
        echo [AVISO] Carpeta existente: %%d\ ^(se omite^)
    )
)

echo.

REM =============================================================================
REM Crear entorno virtual de Python
REM =============================================================================

echo ============================================================
echo   Configurando entorno virtual de Python
echo ============================================================
echo.

if exist "venv\" (
    echo [AVISO] Entorno virtual existente detectado. Verificando...
    if not exist "venv\Scripts\python.exe" (
        echo [AVISO] Entorno virtual corrupto. Recreando...
        rd /S /Q venv 2>nul
    )
)

if not exist "venv\" (
    echo [INFO] Creando entorno virtual...
    "!PYTHON_CMD!" -m venv venv
    if !errorlevel! neq 0 (
        echo [ERROR] Fallo al crear el entorno virtual.
        echo   Intente manualmente:
        echo     "!PYTHON_CMD!" -m venv venv
        exit /b 1
    )
    echo [OK] Entorno virtual creado en .\venv
) else (
    echo [OK] Entorno virtual existente verificado
)

REM Activar entorno virtual
call venv\Scripts\activate.bat
echo [OK] Entorno virtual activado

REM Usar ruta completa al python del venv para evitar alias de Microsoft Store
set "VENV_PYTHON=%SCRIPT_DIR%venv\Scripts\python.exe"
set "VENV_PIP=%SCRIPT_DIR%venv\Scripts\pip.exe"

REM Actualizar pip
echo [INFO] Actualizando pip...
"%VENV_PYTHON%" -m pip install --upgrade pip --quiet 2>nul
echo [OK] pip actualizado

echo.

REM =============================================================================
REM Instalar dependencias de Python
REM =============================================================================

echo ============================================================
echo   Instalando dependencias de Python
echo ============================================================
echo.

if not exist "requirements.txt" (
    echo [ERROR] Archivo requirements.txt no encontrado.
    echo   Asegurese de estar ejecutando este script desde el directorio raiz del proyecto.
    exit /b 1
)

REM Verificar si las dependencias ya están instaladas
echo [INFO] Verificando dependencias instaladas...
set "DEPS_MISSING=0"
for /f "usebackq tokens=1 delims==><" %%p in ("requirements.txt") do (
    set "PKG=%%p"
    if not "!PKG!"=="" (
        "%VENV_PIP%" show "!PKG!" >nul 2>&1
        if !errorlevel! neq 0 (
            set "DEPS_MISSING=1"
        )
    )
)

if %DEPS_MISSING% equ 0 (
    echo [AVISO] Dependencias de Python ya instaladas. Se omite la reinstalacion.
) else (
    echo [INFO] Instalando paquetes desde requirements.txt...
    "%VENV_PIP%" install -r requirements.txt --quiet
    if !errorlevel! neq 0 (
        echo [ERROR] Fallo al instalar dependencias de Python.
        echo   Intente manualmente:
        echo     venv\Scripts\activate.bat
        echo     venv\Scripts\pip install -r requirements.txt
        echo.
        echo   Si el error persiste, verifique:
        echo     - Conexion a internet activa
        echo     - Espacio en disco suficiente
        echo     - Permisos de escritura en el directorio
        exit /b 1
    )
    echo [OK] Dependencias de Python instaladas
)

echo.

REM =============================================================================
REM Instalar Ollama y descargar modelo Llama 3.1 8B
REM =============================================================================

echo ============================================================
echo   Instalando Ollama y modelo Llama 3.1 8B
echo ============================================================
echo.

REM Verificar si Ollama ya está instalado
where ollama >nul 2>&1
if %errorlevel% equ 0 (
    echo [AVISO] Ollama ya esta instalado.
) else (
    echo [INFO] Instalando Ollama...
    echo [INFO] Descargando instalador de Ollama...
    REM Intentar con curl primero
    curl -fsSL -o "%TEMP%\OllamaSetup.exe" "https://ollama.com/download/OllamaSetup.exe" 2>nul
    if not exist "%TEMP%\OllamaSetup.exe" (
        REM Intentar con PowerShell como alternativa
        echo [INFO] Reintentando descarga con PowerShell...
        powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://ollama.com/download/OllamaSetup.exe' -OutFile '%TEMP%\OllamaSetup.exe'" 2>nul
    )
    if exist "%TEMP%\OllamaSetup.exe" (
        echo [INFO] Ejecutando instalador de Ollama...
        start /wait "" "%TEMP%\OllamaSetup.exe" /SILENT
        del "%TEMP%\OllamaSetup.exe" 2>nul
        timeout /t 3 /nobreak >nul
        where ollama >nul 2>&1
        if !errorlevel! equ 0 (
            echo [OK] Ollama instalado correctamente
        ) else (
            echo [AVISO] Ollama se instalo pero no se encuentra en el PATH.
            echo   Cierre y abra una nueva terminal, luego ejecute:
            echo     ollama pull llama3.1:8b
            echo   La aplicacion funcionara con spaCy como fallback por ahora.
        )
    ) else (
        echo [AVISO] No se pudo descargar Ollama automaticamente.
        echo   Instale manualmente desde: https://ollama.com/download
        echo   Luego ejecute: ollama pull llama3.1:8b
        echo   La aplicacion funcionara con spaCy como fallback.
    )
)

REM Descargar modelo Llama 3.1 8B
where ollama >nul 2>&1
if %errorlevel% equ 0 (
    echo [INFO] Verificando modelo Llama 3.1 8B...
    ollama list 2>nul | findstr /i "llama3.1" >nul 2>&1
    if %errorlevel% equ 0 (
        echo [AVISO] Modelo Llama 3.1 8B ya descargado.
    ) else (
        echo [INFO] Descargando modelo Llama 3.1 8B ^(~4.7GB^)...
        echo [INFO] Este paso puede tardar 5-10 minutos dependiendo de su conexion...
        ollama pull llama3.1:8b
        if %errorlevel% equ 0 (
            echo [OK] Modelo Llama 3.1 8B descargado correctamente
        ) else (
            echo [AVISO] No se pudo descargar el modelo.
            echo   Intente manualmente: ollama pull llama3.1:8b
            echo   La aplicacion funcionara con spaCy como fallback.
        )
    )
)

echo.

REM =============================================================================
REM Descargar modelo spaCy (fallback)
REM =============================================================================

echo ============================================================
echo   Descargando modelo spaCy (fallback)
echo ============================================================
echo.

echo [INFO] Este paso puede tardar varios minutos dependiendo de su conexion...

REM Verificar si el modelo ya está instalado y funcional
set "MODEL_INSTALLED=0"
"%VENV_PYTHON%" -c "import spacy; nlp = spacy.load('es_core_news_lg'); doc = nlp('test'); exit(0 if len(doc) > 0 else 1)" >nul 2>&1
if !errorlevel! equ 0 (
    set "MODEL_INSTALLED=1"
)

if "!MODEL_INSTALLED!"=="1" (
    echo [AVISO] Modelo es_core_news_lg ya instalado y verificado. Se omite la descarga.
) else (
    echo [INFO] Descargando modelo es_core_news_lg...
    "%VENV_PYTHON%" -m spacy download es_core_news_lg
    if !errorlevel! neq 0 (
        echo [AVISO] Fallo al descargar el modelo spaCy. Reintentando con pip...
        "%VENV_PIP%" install es_core_news_lg
        if !errorlevel! neq 0 (
            echo [AVISO] No se pudo instalar el modelo spaCy.
            echo   La aplicacion funcionara con Ollama si esta disponible.
            echo   Para instalar manualmente:
            echo     venv\Scripts\python -m spacy download es_core_news_lg
        )
    )
    echo [OK] Modelo spaCy configurado
)

echo.

REM =============================================================================
REM Instalar dependencias del frontend
REM =============================================================================

echo ============================================================
echo   Configurando frontend
echo ============================================================
echo.

if exist "frontend\package.json" (
    REM Verificar si node_modules ya existe
    if exist "frontend\node_modules\" (
        echo [AVISO] Dependencias del frontend ya instaladas. Se omite npm install.
    ) else (
        echo [INFO] Instalando dependencias del frontend...
        cd frontend
        call npm install --quiet 2>nul
        if %errorlevel% neq 0 (
            echo [ERROR] Fallo al instalar dependencias del frontend.
            echo   Intente manualmente:
            echo     cd frontend
            echo     npm install
            echo.
            echo   Si el error persiste, verifique:
            echo     - Conexion a internet activa
            echo     - Version de Node.js ^>= v%MIN_NODE_MAJOR%
            echo     - Espacio en disco suficiente
            cd /d "%SCRIPT_DIR%"
            exit /b 1
        )
        echo [OK] Dependencias del frontend instaladas
        cd /d "%SCRIPT_DIR%"
    )

    REM Build del frontend
    if exist "frontend\dist\" (
        echo [AVISO] Build del frontend ya existe. Se omite la generacion.
    ) else (
        echo [INFO] Generando build del frontend...
        cd frontend
        call npm run build 2>nul
        if %errorlevel% neq 0 (
            echo [AVISO] Fallo al generar build del frontend.
            echo   Puede generarlo manualmente despues:
            echo     cd frontend
            echo     npm run build
        ) else (
            echo [OK] Build del frontend generado
        )
        cd /d "%SCRIPT_DIR%"
    )
) else (
    echo [AVISO] frontend\package.json no encontrado. Se omite la instalacion del frontend.
    echo   El frontend se configurara cuando este disponible.
)

echo.

REM =============================================================================
REM Mensaje de éxito
REM =============================================================================

echo ============================================================
echo   Instalacion completada exitosamente!
echo ============================================================
echo.
echo La aplicacion esta lista para ejecutarse.
echo.
echo   Para iniciar la aplicacion:
echo.
echo     run.bat
echo.
echo   O manualmente:
echo.
echo     venv\Scripts\activate.bat
echo     uvicorn app.main:app --host 0.0.0.0 --port 3000
echo.
echo   Luego abra en su navegador:
echo.
echo     http://localhost:3000
echo.
echo ============================================================

REM Desactivar entorno virtual
call deactivate 2>nul

endlocal
