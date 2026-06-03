# DataMask

**Enmascarar datos sensibles en documentos**

![Version](https://img.shields.io/badge/version-3.2-blue)
![Python](https://img.shields.io/badge/python-≥3.10-green)
![Node](https://img.shields.io/badge/node-≥18-green)
![Platform](https://img.shields.io/badge/platform-macOS%20|%20Windows-lightgrey)

DataMask es una aplicación web local que detecta y enmascara automáticamente datos sensibles (PII) en documentos PDF, Markdown y Word. Corre 100% en tu máquina — ningún dato sale a internet.

## Características

- 🔒 **100% local** — procesamiento offline, sin envío de datos a la nube
- 📄 **Multi-formato** — soporta PDF, Markdown (.md) y Word (.docx)
- 🇦🇷 **Formatos argentinos** — DNI, CUIT/CUIL, teléfonos +54, pasaportes
- 🌍 **Teléfonos internacionales** — detecta cualquier prefijo (+54, +56, +1, etc.)
- ⚙️ **Configurable** — activa/desactiva tipos de datos, edita descripciones, agrega tipos custom con regex
- 🧠 **IA híbrida** — Ollama (Llama 3.1 8B) + patrones regex determinísticos
- 💳 **Tarjetas** — Visa, Mastercard, American Express (15 y 16 dígitos)
- 📑 **Expedientes** — GEDO/TAD (EX-2025-12345678-APN-XXX#YYY)
- 📅 **Fechas** — DD/MM/AA, DD/MM/AAAA, textuales en español
- 📊 **Auditoría** — log detallado de cada archivo procesado
- 🎨 **Interfaz Cloudscape** — UI profesional en español
- 💻 **Multiplataforma** — funciona en macOS, Windows y Linux (EC2)

## Datos que detecta

| Tipo | Etiqueta | Ejemplo |
|------|----------|---------|
| Nombre y Apellido | `[NOMBRE]` | Juan Pérez, MARÍA GARCÍA |
| Email | `[EMAIL]` | usuario@ejemplo.com |
| Teléfono | `[TELEFONO]` | +54 11 4567 8901, +56 9 9440 0259 |
| Celular | `[CELULAR]` | +54 9 11 1234 5678 |
| Dirección | `[DIRECCION]` | Av. Corrientes 1234, CABA |
| DNI | `[DNI]` | 32.456.789 |
| CUIT/CUIL | `[CUIT_CUIL]` | 20-32456789-4 |
| Tarjeta de Crédito | `[TARJETA_CREDITO]` | 4532-1234-5678-9012 |
| Cuenta Bancaria | `[CUENTA_BANCARIA]` | CBU 22 dígitos |
| Pasaporte | `[PASAPORTE]` | AAB123456 |

## Instalación rápida

### macOS

```bash
git clone https://github.com/Eduvilascoder/DataMask.git
cd DataMask
chmod +x setup.sh run.sh stop.sh
./setup.sh
```

### Windows

```cmd
git clone https://github.com/Eduvilascoder/DataMask.git
cd DataMask
setup.bat
```

> ⏱️ La primera instalación tarda ~5 minutos (descarga el modelo de IA de ~560MB).

## Uso

### Iniciar

```bash
./run.sh        # macOS
run.bat         # Windows
```

Abrir en el navegador: **http://localhost:3000**

### Detener

```bash
./stop.sh       # macOS
stop.bat        # Windows
```

## Cómo funciona

1. Seleccioná una carpeta con documentos (PDF, MD, DOCX)
2. Elegí qué archivos procesar
3. DataMask detecta datos sensibles usando IA (spaCy NER + regex)
4. Reemplaza cada dato por una etiqueta `[TIPO]`
5. Genera archivos ofuscados en `ofuscados/` y versiones Markdown en `ofuscados_md/`
6. Los originales **nunca se modifican**

## Estructura del proyecto

```
DataMask/
├── app/                  # Backend Python (FastAPI)
├── frontend/             # Frontend React (Cloudscape)
├── config/               # Configuración de tipos
├── documentacion/        # Documentación completa
├── test/                 # PDFs de ejemplo para pruebas
├── log/                  # Registros de auditoría (generado)
├── ofuscados/            # Documentos ofuscados (generado)
├── ofuscados_md/         # Versiones Markdown (generado)
├── setup.sh / setup.bat  # Instaladores
├── run.sh / run.bat      # Iniciar la app
└── stop.sh / stop.bat    # Detener la app
```

## Requisitos del sistema

- Python >= 3.9
- Node.js >= 18
- 2 GB de espacio en disco (modelo de IA)
- macOS 12+ o Windows 10+

## Seguridad

- El servidor solo escucha en `127.0.0.1` (no accesible desde la red)
- No requiere conexión a internet una vez instalado
- Los archivos originales nunca se modifican
- Ver `documentacion/security_assessment.md` para el assessment completo

## Tecnologías

- **Backend:** Python, FastAPI, spaCy, PyMuPDF, python-docx
- **Frontend:** React, TypeScript, Cloudscape Design System
- **IA:** spaCy `es_core_news_lg` (modelo español) + patrones regex

### Modelo de IA

DataMask usa **spaCy `es_core_news_lg`** — un modelo de procesamiento de lenguaje natural entrenado en español con ~560MB. Es un pipeline CNN (Convolutional Neural Network) entrenado en el corpus AnCora y WikiNER que incluye:

- **NER (Named Entity Recognition):** detecta personas (PER) y ubicaciones (LOC) en texto español
- **F-score NER:** ~0.89 en el benchmark de evaluación
- **Complemento regex:** patrones de expresiones regulares para formatos estructurados (DNI, CUIT, teléfonos, emails, tarjetas, CBU, pasaportes) que el modelo NER no cubre

El modelo se descarga una sola vez durante la instalación y se ejecuta 100% local — no requiere conexión a internet ni envía datos a ningún servidor.

---

**DataMask v1.0** — by [EduTheCoder](https://github.com/Eduvilascoder)
