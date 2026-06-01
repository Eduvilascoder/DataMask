#!/bin/bash
set -e

# =============================================================================
# setup.sh - Instalador para macOS
# Aplicación de Ofuscación de Datos Sensibles en PDFs
# =============================================================================

# Colores para mensajes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # Sin color

# Directorio base del proyecto
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Versiones mínimas requeridas
MIN_PYTHON_MAJOR=3
MIN_PYTHON_MINOR=9
MIN_NODE_MAJOR=18
MIN_DISK_MB=2000  # 2 GB mínimo

# =============================================================================
# Funciones auxiliares
# =============================================================================

print_header() {
    echo ""
    echo -e "${BLUE}============================================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}============================================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ ERROR: $1${NC}"
}

print_info() {
    echo -e "${BLUE}→ $1${NC}"
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        return 1
    fi
    return 0
}

# =============================================================================
# Inicio
# =============================================================================

print_header "Instalador - Ofuscación de Datos Sensibles en PDFs"

echo -e "${BLUE}Sistema operativo: macOS${NC}"
echo -e "${BLUE}Directorio de instalación: $SCRIPT_DIR${NC}"

# =============================================================================
# Verificación de prerequisitos
# =============================================================================

print_header "Verificando prerequisitos del sistema"

# Verificar Python 3
print_info "Verificando Python..."
PYTHON_CMD=""
if check_command python3; then
    PYTHON_CMD="python3"
elif check_command python; then
    # Verificar que no sea Python 2
    PY_VER=$(python --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
    PY_MAJOR=$(echo "$PY_VER" | cut -d. -f1)
    if [ "$PY_MAJOR" -ge 3 ]; then
        PYTHON_CMD="python"
    fi
fi

if [ -z "$PYTHON_CMD" ]; then
    print_info "Python 3 no encontrado. Intentando instalar..."
    if check_command brew; then
        brew install python3
        PYTHON_CMD="python3"
    else
        print_error "No se pudo instalar Python automáticamente (Homebrew no disponible)."
        echo "  Instale Python ${MIN_PYTHON_MAJOR}.${MIN_PYTHON_MINOR} o superior:"
        echo "    1. Instale Homebrew: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        echo "    2. Luego: brew install python3"
        echo "  O descargue desde: https://www.python.org/downloads/"
        exit 1
    fi
fi

# Verificar versión de Python
PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')
PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt "$MIN_PYTHON_MAJOR" ] || { [ "$PYTHON_MAJOR" -eq "$MIN_PYTHON_MAJOR" ] && [ "$PYTHON_MINOR" -lt "$MIN_PYTHON_MINOR" ]; }; then
    print_error "Python $PYTHON_VERSION encontrado, pero se requiere >= $MIN_PYTHON_MAJOR.$MIN_PYTHON_MINOR"
    echo "  Actualice Python:"
    echo "    brew upgrade python3"
    echo "  O descargue desde: https://www.python.org/downloads/"
    exit 1
fi
print_success "Python $PYTHON_VERSION encontrado"

# Verificar Node.js
print_info "Verificando Node.js..."
if ! check_command node; then
    print_info "Node.js no encontrado. Intentando instalar..."
    if check_command brew; then
        brew install node
    else
        print_info "Intentando instalar Node.js via script oficial..."
        curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
        export NVM_DIR="$HOME/.nvm"
        [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
        nvm install 20
    fi
    if ! check_command node; then
        print_error "No se pudo instalar Node.js automáticamente."
        echo "  Instale Node.js ${MIN_NODE_MAJOR} o superior:"
        echo "    brew install node"
        echo "  O descargue desde: https://nodejs.org/"
        exit 1
    fi
    print_success "Node.js instalado correctamente"
fi

NODE_VERSION=$(node --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')
NODE_MAJOR=$(echo "$NODE_VERSION" | cut -d. -f1)

if [ "$NODE_MAJOR" -lt "$MIN_NODE_MAJOR" ]; then
    print_error "Node.js v$NODE_VERSION encontrado, pero se requiere >= v$MIN_NODE_MAJOR"
    echo "  Actualice Node.js:"
    echo "    brew upgrade node"
    echo "  O descargue desde: https://nodejs.org/"
    exit 1
fi
print_success "Node.js v$NODE_VERSION encontrado"

# Verificar npm
print_info "Verificando npm..."
if ! check_command npm; then
    print_error "npm no encontrado."
    echo "  npm se instala junto con Node.js. Reinstale Node.js:"
    echo "    brew reinstall node"
    exit 1
fi
NPM_VERSION=$(npm --version)
print_success "npm v$NPM_VERSION encontrado"

# Verificar espacio en disco
print_info "Verificando espacio en disco..."
AVAILABLE_MB=$(df -m "$SCRIPT_DIR" | awk 'NR==2 {print $4}')
if [ "$AVAILABLE_MB" -lt "$MIN_DISK_MB" ]; then
    print_error "Espacio en disco insuficiente: ${AVAILABLE_MB}MB disponibles, se requieren ${MIN_DISK_MB}MB"
    echo "  Libere espacio en disco antes de continuar."
    exit 1
fi
print_success "Espacio en disco suficiente: ${AVAILABLE_MB}MB disponibles"

# Verificar permisos de escritura
print_info "Verificando permisos de escritura..."
if [ ! -w "$SCRIPT_DIR" ]; then
    print_error "Sin permisos de escritura en el directorio de instalación."
    echo "  Ejecute: chmod u+w \"$SCRIPT_DIR\""
    exit 1
fi
print_success "Permisos de escritura verificados"

# =============================================================================
# Crear estructura de directorios
# =============================================================================

print_header "Creando estructura de directorios"

DIRS=("log" "ofuscados" "test" "documentacion" "models" "config")

for dir in "${DIRS[@]}"; do
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        print_success "Carpeta creada: $dir/"
    else
        print_warning "Carpeta existente: $dir/ (se omite)"
    fi
done

# =============================================================================
# Crear entorno virtual de Python
# =============================================================================

print_header "Configurando entorno virtual de Python"

if [ -d "venv" ]; then
    print_warning "Entorno virtual existente detectado. Se reutilizará."
else
    print_info "Creando entorno virtual..."
    $PYTHON_CMD -m venv venv
    if [ $? -ne 0 ]; then
        print_error "Fallo al crear el entorno virtual."
        echo "  Intente manualmente:"
        echo "    $PYTHON_CMD -m venv venv"
        exit 1
    fi
    print_success "Entorno virtual creado en ./venv"
fi

# Activar entorno virtual
source venv/bin/activate
print_success "Entorno virtual activado"

# Actualizar pip
print_info "Actualizando pip..."
pip install --upgrade pip --quiet
print_success "pip actualizado"

# =============================================================================
# Instalar dependencias de Python
# =============================================================================

print_header "Instalando dependencias de Python"

if [ ! -f "requirements.txt" ]; then
    print_error "Archivo requirements.txt no encontrado."
    echo "  Asegúrese de estar ejecutando este script desde el directorio raíz del proyecto."
    exit 1
fi

# Verificar si las dependencias ya están instaladas
print_info "Verificando dependencias instaladas..."
DEPS_INSTALLED=true
while IFS= read -r line || [ -n "$line" ]; do
    # Ignorar líneas vacías y comentarios
    line=$(echo "$line" | sed 's/#.*//' | xargs)
    [ -z "$line" ] && continue
    # Extraer nombre del paquete (antes de ==, >=, etc.)
    PKG_NAME=$(echo "$line" | sed 's/[>=<].*//')
    if ! pip show "$PKG_NAME" &>/dev/null; then
        DEPS_INSTALLED=false
        break
    fi
done < requirements.txt

if [ "$DEPS_INSTALLED" = true ]; then
    print_warning "Dependencias de Python ya instaladas. Se omite la reinstalación."
else
    print_info "Instalando paquetes desde requirements.txt..."
    if ! pip install -r requirements.txt --quiet; then
        print_error "Fallo al instalar dependencias de Python."
        echo "  Intente manualmente:"
        echo "    source venv/bin/activate"
        echo "    pip install -r requirements.txt"
        echo ""
        echo "  Si el error persiste, verifique:"
        echo "    - Conexión a internet activa"
        echo "    - Espacio en disco suficiente"
        echo "    - Permisos de escritura en el directorio"
        exit 1
    fi
    print_success "Dependencias de Python instaladas"
fi

# =============================================================================
# Instalar Ollama y descargar modelo Llama 3.1 8B
# =============================================================================

print_header "Instalando Ollama y modelo Llama 3.1 8B"

# Verificar si Ollama ya está instalado
if check_command ollama; then
    print_warning "Ollama ya está instalado."
else
    print_info "Instalando Ollama..."
    if curl -fsSL https://ollama.com/install.sh | sh; then
        print_success "Ollama instalado correctamente"
    else
        print_error "No se pudo instalar Ollama automáticamente."
        echo "  Instale manualmente desde: https://ollama.com/download"
        echo "  Luego ejecute: ollama pull llama3.1:8b"
        echo ""
        echo "  La aplicación funcionará con spaCy como fallback."
    fi
fi

# Descargar modelo Llama 3.1 8B si Ollama está disponible
if check_command ollama; then
    # Verificar si el modelo ya está descargado
    if ollama list 2>/dev/null | grep -q "llama3.1"; then
        print_warning "Modelo Llama 3.1 8B ya descargado."
    else
        print_info "Descargando modelo Llama 3.1 8B (~4.7GB)..."
        print_info "Este paso puede tardar 5-10 minutos dependiendo de su conexión..."
        if ollama pull llama3.1:8b; then
            print_success "Modelo Llama 3.1 8B descargado correctamente"
        else
            print_error "No se pudo descargar el modelo."
            echo "  Intente manualmente: ollama pull llama3.1:8b"
            echo "  La aplicación funcionará con spaCy como fallback."
        fi
    fi
fi

# =============================================================================
# Descargar modelo spaCy (fallback)
# =============================================================================

print_header "Descargando modelo spaCy (fallback)"

print_info "Este paso puede tardar varios minutos dependiendo de su conexión..."

# Verificar si el modelo ya está instalado
MODEL_INSTALLED=false
if python -c "import spacy; spacy.load('es_core_news_lg')" 2>/dev/null; then
    MODEL_INSTALLED=true
fi

if [ "$MODEL_INSTALLED" = true ]; then
    print_warning "Modelo es_core_news_lg ya instalado. Se omite la descarga."
    # Verificar integridad del modelo cargándolo
    print_info "Verificando integridad del modelo..."
    if python -c "
import spacy
import sys
try:
    nlp = spacy.load('es_core_news_lg')
    # Verificar que el modelo puede procesar texto
    doc = nlp('Prueba de verificación del modelo.')
    if len(doc) > 0:
        sys.exit(0)
    else:
        sys.exit(1)
except Exception as e:
    print(f'Error al verificar modelo: {e}', file=sys.stderr)
    sys.exit(1)
"; then
        print_success "Integridad del modelo verificada correctamente"
    else
        print_warning "El modelo existente parece corrupto. Reinstalando..."
        MODEL_INSTALLED=false
    fi
fi

if [ "$MODEL_INSTALLED" = false ]; then
    print_info "Descargando modelo es_core_news_lg..."
    if ! python -m spacy download es_core_news_lg; then
        print_error "Fallo al descargar el modelo spaCy es_core_news_lg."
        echo ""
        echo "  Posibles causas:"
        echo "    - Sin conexión a internet"
        echo "    - Espacio en disco insuficiente (el modelo requiere ~560MB)"
        echo "    - Interrupción de la descarga"
        echo ""
        echo "  Para reintentar manualmente:"
        echo "    source venv/bin/activate"
        echo "    python -m spacy download es_core_news_lg"
        exit 1
    fi

    # Verificar integridad post-descarga
    print_info "Verificando integridad del modelo descargado..."
    if python -c "
import spacy
import sys
try:
    nlp = spacy.load('es_core_news_lg')
    doc = nlp('Verificación post-instalación del modelo NER.')
    if len(doc) > 0 and nlp.meta.get('name') == 'core_news_lg':
        sys.exit(0)
    else:
        sys.exit(1)
except Exception as e:
    print(f'Error: {e}', file=sys.stderr)
    sys.exit(1)
"; then
        print_success "Modelo es_core_news_lg descargado y verificado correctamente"
    else
        print_error "El modelo descargado no pasó la verificación de integridad."
        echo "  El archivo puede estar corrupto. Intente:"
        echo "    source venv/bin/activate"
        echo "    pip uninstall es_core_news_lg -y"
        echo "    python -m spacy download es_core_news_lg"
        exit 1
    fi
fi

# =============================================================================
# Instalar dependencias del frontend
# =============================================================================

print_header "Configurando frontend"

if [ -f "frontend/package.json" ]; then
    # Verificar si node_modules ya existe
    if [ -d "frontend/node_modules" ]; then
        print_warning "Dependencias del frontend ya instaladas. Se omite npm install."
    else
        print_info "Instalando dependencias del frontend..."
        if ! npm install --prefix frontend --quiet 2>/dev/null; then
            print_error "Fallo al instalar dependencias del frontend."
            echo "  Intente manualmente:"
            echo "    cd frontend && npm install"
            echo ""
            echo "  Si el error persiste, verifique:"
            echo "    - Conexión a internet activa"
            echo "    - Versión de Node.js >= ${MIN_NODE_MAJOR}"
            echo "    - Espacio en disco suficiente"
            exit 1
        fi
        print_success "Dependencias del frontend instaladas"
    fi

    # Build del frontend
    if [ -d "frontend/dist" ]; then
        print_warning "Build del frontend ya existe. Se omite la generación."
    else
        print_info "Generando build del frontend..."
        if ! npm run build --prefix frontend 2>/dev/null; then
            print_warning "Fallo al generar build del frontend."
            echo "  Puede generarlo manualmente después:"
            echo "    cd frontend && npm run build"
        else
            print_success "Build del frontend generado"
        fi
    fi
else
    print_warning "frontend/package.json no encontrado. Se omite la instalación del frontend."
    echo "  El frontend se configurará cuando esté disponible."
fi

# =============================================================================
# Mensaje de éxito
# =============================================================================

print_header "¡Instalación completada exitosamente!"

echo -e "${GREEN}La aplicación está lista para ejecutarse.${NC}"
echo ""
echo "  Para iniciar la aplicación:"
echo ""
echo -e "    ${BLUE}./run.sh${NC}"
echo ""
echo "  O manualmente:"
echo ""
echo -e "    source venv/bin/activate"
echo -e "    uvicorn app.main:app --host 0.0.0.0 --port 3000"
echo ""
echo "  Luego abra en su navegador:"
echo ""
echo -e "    ${BLUE}http://localhost:3000${NC}"
echo ""
echo -e "${GREEN}============================================================${NC}"

# Desactivar entorno virtual
deactivate 2>/dev/null || true
