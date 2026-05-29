#!/bin/bash
# =============================================================================
# stop.sh - Detener la aplicación DataMask en macOS
# =============================================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}  DataMask — Deteniendo servidor${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""

# Buscar proceso uvicorn de la app
PIDS=$(pgrep -f "uvicorn app.main:app" 2>/dev/null)

if [ -z "$PIDS" ]; then
    echo -e "${RED}✗ No se encontró ningún proceso de DataMask en ejecución.${NC}"
    echo ""
    exit 0
fi

# Detener todos los procesos encontrados
for PID in $PIDS; do
    echo -e "${GREEN}→ Deteniendo proceso PID: $PID${NC}"
    kill "$PID" 2>/dev/null
done

# Esperar un momento y verificar
sleep 2

REMAINING=$(pgrep -f "uvicorn app.main:app" 2>/dev/null)
if [ -z "$REMAINING" ]; then
    echo ""
    echo -e "${GREEN}✓ DataMask detenido correctamente.${NC}"
else
    echo -e "${RED}⚠ Algunos procesos no se detuvieron. Forzando...${NC}"
    for PID in $REMAINING; do
        kill -9 "$PID" 2>/dev/null
    done
    echo -e "${GREEN}✓ Procesos forzados a detenerse.${NC}"
fi

echo ""
