#!/bin/bash
# =============================================================================
# runEC2.sh — Levanta DataMask en 0.0.0.0:3000 (accesible externamente)
# Uso: chmod +x runEC2.sh && ./runEC2.sh
# =============================================================================

set -e

PORT=${PORT:-3000}
HOST="0.0.0.0"

echo "============================================"
echo "  DataMask v3.2 — Servidor EC2"
echo "  Escuchando en: http://${HOST}:${PORT}"
echo "============================================"
echo ""

# Activar venv
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    echo "❌ ERROR: No se encontró venv/. Ejecute ./setupEC2.sh primero."
    exit 1
fi

# Verificar si Ollama está corriendo
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✅ Ollama está corriendo"
else
    echo "⚠️  Ollama no está corriendo. DataMask usará solo regex + spaCy."
    echo "   Para iniciar Ollama: ollama serve &"
    echo ""
fi

# Levantar uvicorn en 0.0.0.0
echo ">>> Iniciando servidor en http://${HOST}:${PORT}..."
echo ""
uvicorn app.main:app --host ${HOST} --port ${PORT}
