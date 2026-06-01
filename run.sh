#!/bin/bash
# =============================================================================
# run.sh - Iniciar la aplicación en macOS
# Aplicación de Ofuscación de Datos Sensibles en PDFs
# =============================================================================

set -e

# Colores para mensajes
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# Directorio base del proyecto
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Puerto por defecto
PORT=${PORT:-3000}
HOST=${HOST:-127.0.0.1}

echo ""
echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}  Ofuscación de Datos Sensibles en PDFs${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""

# Verificar que el entorno virtual existe
if [ ! -d "venv" ]; then
    echo -e "${RED}✗ ERROR: Entorno virtual no encontrado.${NC}"
    echo "  Ejecute primero el instalador:"
    echo "    ./setup.sh"
    exit 1
fi

# Activar entorno virtual
source venv/bin/activate

# Verificar que uvicorn está disponible
if ! command -v uvicorn &> /dev/null; then
    echo -e "${RED}✗ ERROR: uvicorn no encontrado en el entorno virtual.${NC}"
    echo "  Ejecute el instalador para instalar las dependencias:"
    echo "    ./setup.sh"
    exit 1
fi

# Crear carpetas necesarias si no existen
mkdir -p log ofuscados ofuscados_md test documentacion models config

# Iniciar Ollama en background si está disponible
if command -v ollama &> /dev/null; then
    if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo -e "${GREEN}→ Iniciando Ollama en background...${NC}"
        ollama serve > /dev/null 2>&1 &
        sleep 2
    fi
    echo -e "${GREEN}→ Ollama activo (Llama 3.1 8B)${NC}"
else
    echo -e "${BLUE}→ Ollama no instalado — usando spaCy como fallback${NC}"
fi

echo -e "${GREEN}→ Iniciando servidor en http://localhost:${PORT}${NC}"
echo -e "${GREEN}→ Presione Ctrl+C para detener el servidor${NC}"
echo ""

# Iniciar uvicorn
uvicorn app.main:app --host "$HOST" --port "$PORT"
