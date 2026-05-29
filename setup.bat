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

where python >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_CMD=python"
) else (
    where python3 >nul 2>&1
    if %errorlevel% equ 0 (
        set "PYTHON_CMD=python3"
    )
)

if "%PYTHON_CMD%"=="" (
    echo [ERROR] Python no encontrado.
    echo   Instale Python %MIN_PYTHON_MAJOR%.%MIN_PYTHON_MINOR% o superior desde:
    echo     https://www.python.org/downloads/
    echo   Asegurese de marcar "Add Python to PATH" durante la instalacion.
    exit /b 1
)

REM Verificar versión de Python
for /f "tokens=2 delims= " %%v in ('%PYTHON_CMD% --version 2^>^&1') do set "PYTHON_VERSION=%%v"
for /f "tokens=1,2 delims=." %%a in ("%PYTHON_VERSION%") do (
    set "PY_MAJOR=%%a"
    set "PY_MINOR=%%b"
)

if %PY_MAJOR% lss %MIN_PYTHON_MAJOR% (
    echo [ERROR] Python %PYTHON_VERSION% encontrado, pero se requiere ^>= %MIN_PYTHON_MAJOR%.%MIN_PYTHON_MINOR%
    echo   Descargue la version mas reciente desde:
    echo     https://www.python.org/downloads/
    exit /b 1
)
if %PY_MAJOR% equ %MIN_PYTHON_MAJOR% (
    if %PY_MINOR% lss %MIN_PYTHON_MINOR% (
        echo [ERROR] Python %PYTHON_VERSION% encontrado, pero se requiere ^>= %MIN_PYTHON_MAJOR%.%MIN_PYTHON_MINOR%
        echo   Descargue la version mas reciente desde:
        echo     https://www.python.org/downloads/
        exit /b 1
    )
)
echo [OK] Python %PYTHON_VERSION% encontrado

REM Verificar Node.js
echo [INFO] Verificando Node.js...
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js no encontrado.
    echo   Instale Node.js %MIN_NODE_MAJOR% o superior desde:
    echo     https://nodejs.org/
    exit /b 1
)

for /f "tokens=1 delims=." %%a in ('node --version') do set "NODE_VERSION_RAW=%%a"
REM Eliminar el prefijo 'v' del major version
set "NODE_MAJOR=%NODE_VERSION_RAW:v=%"

for /f "delims=" %%v in ('node --version') do set "NODE_VERSION_DISPLAY=%%v"

if %NODE_MAJOR% lss %MIN_NODE_MAJOR% (
    echo [ERROR] Node.js %NODE_VERSION_DISPLAY% encontrado, pero se requiere ^>= v%MIN_NODE_MAJOR%
    echo   Descargue la version mas reciente desde:
    echo     https://nodejs.org/
    exit /b 1
)
echo [OK] Node.js %NODE_VERSION_DISPLAY% encontrado

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
    echo [AVISO] Entorno virtual existente detectado. Se reutilizara.
) else (
    echo [INFO] Creando entorno virtual...
    %PYTHON_CMD% -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Fallo al crear el entorno virtual.
        echo   Intente manualmente:
        echo     %PYTHON_CMD% -m venv venv
        exit /b 1
    )
    echo [OK] Entorno virtual creado en .\venv
)

REM Activar entorno virtual
call venv\Scripts\activate.bat
echo [OK] Entorno virtual activado

REM Actualizar pip
echo [INFO] Actualizando pip...
python -m pip install --upgrade pip --quiet
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
        pip show "!PKG!" >nul 2>&1
        if !errorlevel! neq 0 (
            set "DEPS_MISSING=1"
        )
    )
)

if %DEPS_MISSING% equ 0 (
    echo [AVISO] Dependencias de Python ya instaladas. Se omite la reinstalacion.
) else (
    echo [INFO] Instalando paquetes desde requirements.txt...
    pip install -r requirements.txt --quiet
    if %errorlevel% neq 0 (
        echo [ERROR] Fallo al instalar dependencias de Python.
        echo   Intente manualmente:
        echo     venv\Scripts\activate.bat
        echo     pip install -r requirements.txt
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
REM Descargar modelo spaCy con verificación de integridad
REM =============================================================================

echo ============================================================
echo   Descargando modelo de IA (spaCy es_core_news_lg)
echo ============================================================
echo.

echo [INFO] Este paso puede tardar varios minutos dependiendo de su conexion...

REM Verificar si el modelo ya está instalado y funcional
set "MODEL_INSTALLED=0"
python -c "import spacy; nlp = spacy.load('es_core_news_lg'); doc = nlp('test'); exit(0 if len(doc) > 0 else 1)" >nul 2>&1
if %errorlevel% equ 0 (
    set "MODEL_INSTALLED=1"
)

if %MODEL_INSTALLED% equ 1 (
    echo [AVISO] Modelo es_core_news_lg ya instalado y verificado. Se omite la descarga.
) else (
    echo [INFO] Descargando modelo es_core_news_lg...
    python -m spacy download es_core_news_lg
    if %errorlevel% neq 0 (
        echo [ERROR] Fallo al descargar el modelo spaCy es_core_news_lg.
        echo.
        echo   Posibles causas:
        echo     - Sin conexion a internet
        echo     - Espacio en disco insuficiente ^(el modelo requiere ~560MB^)
        echo     - Interrupcion de la descarga
        echo.
        echo   Para reintentar manualmente:
        echo     venv\Scripts\activate.bat
        echo     python -m spacy download es_core_news_lg
        exit /b 1
    )

    REM Verificar integridad post-descarga
    echo [INFO] Verificando integridad del modelo descargado...
    python -c "import spacy; nlp = spacy.load('es_core_news_lg'); doc = nlp('Verificacion post-instalacion.'); assert len(doc) > 0 and nlp.meta.get('name') == 'core_news_lg'" >nul 2>&1
    if %errorlevel% neq 0 (
        echo [ERROR] El modelo descargado no paso la verificacion de integridad.
        echo   El archivo puede estar corrupto. Intente:
        echo     venv\Scripts\activate.bat
        echo     pip uninstall es_core_news_lg -y
        echo     python -m spacy download es_core_news_lg
        exit /b 1
    )
    echo [OK] Modelo es_core_news_lg descargado y verificado correctamente
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
