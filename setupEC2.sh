#!/bin/bash
# =============================================================================
# setupEC2.sh — Instala DataMask en Amazon Linux 2023 / EC2
# Requiere: instancia con al menos 8 GB RAM (para Ollama + spaCy)
# Uso: chmod +x setupEC2.sh && ./setupEC2.sh
# =============================================================================

set -e

echo "============================================"
echo "  DataMask v3.2 — Setup para EC2"
echo "============================================"
echo ""

# 1. Instalar Python 3.11 (spaCy requiere >=3.10)
echo ">>> Instalando Python 3.11..."
if command -v python3.11 &>/dev/null; then
    echo "    Python 3.11 ya instalado: $(python3.11 --version)"
else
    sudo dnf install python3.11 python3.11-pip python3.11-devel -y 2>/dev/null || \
    sudo yum install python3.11 python3.11-pip python3.11-devel -y 2>/dev/null || \
    {
        echo "❌ No se pudo instalar python3.11 con dnf/yum."
        echo "   Intentando con amazon-linux-extras..."
        sudo amazon-linux-extras enable python3.11 2>/dev/null && \
        sudo yum install python3.11 python3.11-pip python3.11-devel -y || \
        {
            echo "❌ ERROR: No se pudo instalar Python 3.11."
            echo "   Instálelo manualmente o use una AMI con Python 3.11+."
            exit 1
        }
    }
    echo "    ✅ Python instalado: $(python3.11 --version)"
fi

# 2. Instalar Node.js 20 (para build del frontend)
echo ""
echo ">>> Instalando Node.js 20..."
if command -v node &>/dev/null; then
    echo "    Node.js ya instalado: $(node --version)"
else
    curl -fsSL https://rpm.nodesource.com/setup_20.x | sudo bash - 2>/dev/null
    sudo dnf install nodejs -y 2>/dev/null || sudo yum install nodejs -y
    echo "    ✅ Node.js instalado: $(node --version)"
fi

# 3. Instalar git si no está
if ! command -v git &>/dev/null; then
    echo ""
    echo ">>> Instalando git..."
    sudo dnf install git -y 2>/dev/null || sudo yum install git -y
fi

# 4. Crear venv con Python 3.11
echo ""
echo ">>> Creando virtual environment con Python 3.11..."
if [ -d "venv" ]; then
    rm -rf venv
fi
python3.11 -m venv venv
source venv/bin/activate

# 5. Instalar dependencias Python
echo ""
echo ">>> Instalando dependencias Python..."
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# 6. Descargar modelo spaCy en español
echo ""
echo ">>> Descargando modelo spaCy es_core_news_lg..."
python -m spacy download es_core_news_lg 2>/dev/null || \
    pip install https://github.com/explosion/spacy-models/releases/download/es_core_news_lg-3.8.0/es_core_news_lg-3.8.0-py3-none-any.whl 2>/dev/null || \
    echo "⚠️  No se pudo instalar es_core_news_lg. DataMask funcionará sin spaCy (solo Ollama + regex)."

# 7. Build del frontend
echo ""
echo ">>> Compilando frontend..."
if [ -d "frontend" ]; then
    cd frontend
    npm install
    npm run build
    cd ..
    echo "    ✅ Frontend compilado"
else
    echo "    ⚠️  Carpeta frontend/ no encontrada. Saltando build."
fi

# 8. Instalar Ollama (opcional pero recomendado)
echo ""
echo ">>> Instalando Ollama..."
if command -v ollama &>/dev/null; then
    echo "    Ollama ya instalado."
else
    curl -fsSL https://ollama.com/install.sh | sh
    echo "    ✅ Ollama instalado"
fi

# 9. Crear carpetas necesarias
echo ""
echo ">>> Creando carpetas..."
mkdir -p log ofuscados ofuscados_md test documentacion models config

# 10. Resumen
echo ""
echo "============================================"
echo "  ✅ Setup completado"
echo "============================================"
echo ""
echo "Próximos pasos:"
echo ""
echo "  1. Iniciar Ollama y descargar el modelo:"
echo "     ollama serve &"
echo "     ollama pull llama3.1:8b"
echo ""
echo "  2. Ejecutar DataMask:"
echo "     ./runEC2.sh"
echo ""
echo "  3. Abrir puerto 3000 en el Security Group de la EC2"
echo "     y acceder desde: http://<IP_PUBLICA>:3000"
echo ""
