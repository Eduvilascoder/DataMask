# DataMask

**Enmascarar datos sensibles en documentos**

![Version](https://img.shields.io/badge/version-3.2.2-blue)
![Python](https://img.shields.io/badge/python-≥3.10-green)
![Node](https://img.shields.io/badge/node-≥18-green)
![Platform](https://img.shields.io/badge/platform-macOS%20|%20Windows-lightgrey)

DataMask es una aplicación web local que detecta y enmascara automáticamente datos sensibles (PII) en documentos PDF, Markdown y Word. Corre 100% en tu máquina — ningún dato sale a internet.

## Características

- 🔒 **100% local** — procesamiento offline, sin envío de datos a la nube
- 📄 **Multi-formato** — soporta PDF, Markdown (.md) y Word (.docx)
- 🇦🇷 **Formatos argentinos** — DNI, CUIT/CUIL, teléfonos +54, celulares locales (11)..., pasaportes
- 🌍 **Teléfonos internacionales** — detecta cualquier prefijo (+54, +56, +1, etc.)
- ⚙️ **Configurable** — activa/desactiva tipos de datos, edita descripciones, agrega tipos custom con regex
- 🧠 **IA híbrida** — Ollama (modelo configurable) + patrones regex determinísticos, con spaCy como fallback
- 🔀 **Modelo seleccionable** — elegí el modelo de Ollama desde la UI (llama3.1:8b, qwen2.5:7b, etc.) y descargá nuevos modelos sin salir de la app
- 💳 **Tarjetas** — Visa, Mastercard, American Express (15 y 16 dígitos)
- 📑 **Expedientes** — GEDO/TAD (EX-2025-12345678-APN-XXX#YYY)
- 📅 **Fechas** — DD/MM/AA, DD/MM/AAAA, textuales en español
- ⏱️ **Timer y cancelación** — tiempo de procesamiento en vivo y botón para cancelar el proceso
- 📊 **Auditoría** — log detallado de cada archivo: motor y modelo usado, tiempo de procesamiento, volumen y detalle de error
- 🎨 **Interfaz Cloudscape** — UI profesional en español
- 💻 **Multiplataforma** — funciona en macOS, Windows y Linux (EC2)

## Datos que detecta

| Tipo | Etiqueta | Ejemplo |
|------|----------|---------|
| Nombre y Apellido | `[NOMBRE]` | Juan Pérez, MARÍA GARCÍA |
| Email | `[EMAIL]` | usuario@ejemplo.com |
| Teléfono | `[TELEFONO]` | +54 11 4567 8901, +56 9 9440 0259 |
| Celular | `[CELULAR]` | +54 9 11 1234 5678, (11)34306563 |
| Dirección | `[DIRECCION]` | Av. Corrientes 1234, CABA, GRANADEROS 457 5 G |
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
3. DataMask detecta datos sensibles usando IA (Ollama o spaCy) + regex
4. Reemplaza cada dato por una etiqueta `[TIPO]`
5. Genera archivos ofuscados en `ofuscados/` y versiones Markdown en `ofuscados_md/`
6. Los originales **nunca se modifican**

## Estructura del proyecto

```
DataMask/
├── app/                  # Backend Python (FastAPI)
├── frontend/             # Frontend React (Cloudscape)
├── config/               # Configuración (tipos, Ollama, spaCy)
├── documentacion/        # Documentación completa
├── test/                 # PDFs de ejemplo para pruebas
├── log/                  # Registros de auditoría (generado)
├── ofuscados/            # Documentos ofuscados (generado)
├── ofuscados_md/         # Versiones Markdown (generado)
├── setup.sh / setup.bat  # Instaladores
├── run.sh / run.bat      # Iniciar la app
└── stop.sh / stop.bat    # Detener la app
```

> La carpeta `config/` contiene tres archivos: `types_config.json` (tipos de datos sensibles y prompt), `ollama.json` (modelo, temperatura, keep_alive) y `spacy.json` (modelo spaCy).

## Requisitos del sistema

- Python >= 3.10
- Node.js >= 18
- Ollama (opcional, recomendado para máxima precisión)
- 8 GB de RAM recomendado si se usa Ollama
- macOS 12+, Windows 10+ o Linux

## Seguridad

- El servidor solo escucha en `127.0.0.1` (no accesible desde la red)
- No requiere conexión a internet una vez instalado
- Los archivos originales nunca se modifican
- Ver `documentacion/security_assessment.md` para el assessment completo

## Tecnologías

- **Backend:** Python, FastAPI, spaCy, PyMuPDF, python-docx
- **Frontend:** React, TypeScript, Cloudscape Design System
- **IA:** Ollama (modelo configurable) + spaCy `es_core_news_lg` (fallback) + patrones regex

### Motor de IA

DataMask usa un enfoque híbrido con dos motores intercambiables más patrones regex:

- **Ollama (recomendado):** ejecuta un LLM local (por defecto `llama3.1:8b`, configurable). Entiende el contexto semántico del texto, por lo que detecta nombres en mayúsculas, nombres poco comunes y direcciones complejas con alta precisión. El modelo se elige desde la página de Configuración y se puede descargar uno nuevo sin salir de la app.
- **spaCy `es_core_news_lg`:** pipeline CNN entrenado en español (~560MB). Es el fallback automático cuando Ollama no está disponible, o se puede elegir manualmente cuando se prioriza velocidad sobre precisión.
- **Patrones regex:** complemento determinístico para formatos estructurados (DNI, CUIT, teléfonos, celulares locales, emails, tarjetas, CBU, pasaportes, expedientes) con detección de ~100% de precisión.

Todo se ejecuta 100% local — no requiere conexión a internet ni envía datos a ningún servidor. Ver `documentacion/motorIA.md` para la comparación detallada entre Ollama y spaCy.

---

**DataMask v3.2.2** — by [EduTheCoder](https://github.com/Eduvilascoder)
