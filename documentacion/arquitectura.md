# Arquitectura del Sistema

## Descripción General

La aplicación de Ofuscación de Datos Sensibles en PDFs es una herramienta local que permite detectar y reemplazar información personal identificable en archivos PDF. La arquitectura sigue un patrón cliente-servidor donde todos los componentes se ejecutan en la máquina del usuario, sin dependencias de servicios en la nube.

---

## Componentes Principales

### 1. Backend (FastAPI)

El servidor backend maneja toda la lógica de negocio: validación de rutas, procesamiento de PDFs, detección de entidades y gestión de configuración.

- **Framework**: FastAPI 0.115.6
- **Servidor ASGI**: Uvicorn 0.34.0
- **Puerto por defecto**: 3000
- **Responsabilidades**:
  - Servir la API REST para el frontend
  - Servir los archivos estáticos del build de React
  - Orquestar el flujo de procesamiento de PDFs
  - Gestionar la configuración persistente de tipos
  - Registrar auditoría de operaciones

### 2. Frontend (React + Cloudscape)

La interfaz de usuario está construida con React y el sistema de diseño Cloudscape de AWS, presentada completamente en español.

- **Framework**: React 18.2
- **Componentes UI**: Cloudscape Design System 3.x
- **Bundler**: Vite 5.x
- **Lenguaje**: TypeScript 5.3
- **Responsabilidades**:
  - Interfaz para selección de carpeta de PDFs
  - Panel de configuración de tipos de datos sensibles
  - Visualización de progreso en tiempo real (SSE)
  - Visor de registros de auditoría

### 3. Motor NER (Ollama / spaCy + Regex)

El motor de reconocimiento de entidades nombradas combina un modelo de lenguaje (LLM vía Ollama) o un modelo NLP (spaCy) como fallback, con patrones regex específicos para formatos argentinos.

- **Motor primario**: Ollama con modelo configurable (por defecto `llama3.1:8b`), accedido vía HTTP en `localhost:11434`
- **Motor fallback**: spaCy `es_core_news_lg` (español, ~560MB), usado cuando Ollama no está disponible o si el usuario lo elige
- **Patrones Regex**: Expresiones regulares para DNI, CUIT/CUIL, teléfonos, celulares locales, emails, tarjetas de crédito, CBU, pasaportes y expedientes
- **Umbral de confianza**: 0.70 mínimo para incluir una detección
- **Responsabilidades**:
  - Detectar nombres y direcciones mediante Ollama (semántico) o spaCy (estadístico)
  - Detectar formatos estructurados mediante regex (cargados desde `types_config.json`)
  - Resolver conflictos cuando un dato coincide con múltiples tipos
  - Filtrar detecciones según la configuración de tipos activos

### 4. Procesador PDF (PyMuPDF)

El componente de procesamiento de PDFs se encarga de la extracción de texto y la aplicación de redacciones.

- **Librería**: PyMuPDF (fitz) 1.25.1
- **Responsabilidades**:
  - Extraer texto de cada página del PDF
  - Localizar las posiciones exactas del texto sensible
  - Aplicar redacciones reemplazando texto por Etiquetas_Ofuscación
  - Generar el PDF ofuscado preservando la estructura original
  - Guardar el archivo resultante en la Carpeta_Ofuscados

---

## Tecnologías Utilizadas

| Componente | Tecnología | Versión |
|------------|-----------|---------|
| Backend Framework | FastAPI | 0.115.6 |
| Servidor ASGI | Uvicorn | 0.34.0 |
| Procesamiento PDF | PyMuPDF (fitz) | 1.25.1 |
| Procesamiento Word | python-docx | >= 1.1.0 |
| Motor IA primario | Ollama (LLM local) | modelo configurable |
| Motor NER fallback | spaCy | 3.8.3 |
| Modelo NER español | es_core_news_lg | compatible con spaCy 3.8 |
| Cliente HTTP (Ollama) | httpx | 0.28.1 |
| Validación de datos | Pydantic | 2.10.4 |
| Generación de PDFs test | fpdf2 | 2.8.2 |
| Frontend Framework | React | 18.2.x |
| Componentes UI | Cloudscape Design System | 3.x |
| Router Frontend | React Router DOM | 6.20.x |
| Bundler | Vite | 5.x |
| Lenguaje Frontend | TypeScript | 5.3.x |
| Runtime | Python | >= 3.10 |
| Runtime Frontend | Node.js | >= 18 |

---

## Flujo de Procesamiento de PDFs

```
┌─────────────────────────────────────────────────────────────────────┐
│                    FLUJO DE PROCESAMIENTO                            │
└─────────────────────────────────────────────────────────────────────┘

  ┌──────────┐     ┌──────────────┐     ┌───────────────────┐
  │ Usuario  │────▶│   Frontend   │────▶│  Backend (API)    │
  │          │     │  (React)     │     │  POST /api/process│
  └──────────┘     └──────────────┘     └─────────┬─────────┘
                                                   │
                          ┌────────────────────────┘
                          ▼
              ┌───────────────────────┐
              │  Para cada archivo PDF │◀─────────────────────┐
              └───────────┬───────────┘                       │
                          │                                   │
                          ▼                                   │
              ┌───────────────────────┐                       │
              │  Extraer texto por    │                       │
              │  página (PyMuPDF)     │                       │
              └───────────┬───────────┘                       │
                          │                                   │
                          ▼                                   │
              ┌───────────────────────┐                       │
              │  Detectar entidades   │                       │
              │  sensibles (NER)      │                       │
              │  • Ollama (nombres,   │                       │
              │    direcciones) o     │                       │
              │    spaCy (fallback)   │                       │
              │  • Regex (DNI, email, │                       │
              │    teléfono, etc.)    │                       │
              └───────────┬───────────┘                       │
                          │                                   │
                          ▼                                   │
              ┌───────────────────────┐                       │
              │  Filtrar por umbral   │                       │
              │  de confianza >= 0.70 │                       │
              └───────────┬───────────┘                       │
                          │                                   │
                          ▼                                   │
              ┌───────────────────────┐                       │
              │  Aplicar redacciones  │                       │
              │  [NOMBRE], [EMAIL],   │                       │
              │  [DNI], etc.          │                       │
              └───────────┬───────────┘                       │
                          │                                   │
                          ▼                                   │
              ┌───────────────────────┐                       │
              │  Guardar PDF ofuscado │                       │
              │  en ofuscados/        │                       │
              │  (sufijo _ofuscado)   │                       │
              └───────────┬───────────┘                       │
                          │                                   │
                          ▼                                   │
              ┌───────────────────────┐                       │
              │  Registrar en log     │                       │
              │  de auditoría         │                       │
              └───────────┬───────────┘                       │
                          │                                   │
                          ▼                                   │
              ┌───────────────────────┐                       │
              │  Enviar progreso      │───────────────────────┘
              │  al frontend (SSE)    │   (siguiente archivo)
              └───────────────────────┘
```

---

## Estructura de Carpetas del Proyecto

```
PDF-Datos-Sensibles/
├── app/                          # Backend Python (FastAPI)
│   ├── __init__.py
│   ├── main.py                   # Entry point del servidor
│   ├── models.py                 # Modelos Pydantic compartidos
│   ├── exceptions.py             # Clases de error personalizadas
│   ├── api/                      # Capa de rutas API
│   │   ├── __init__.py
│   │   ├── routes.py             # Endpoints REST
│   │   └── file_service.py       # Servicio de archivos
│   ├── ner/                      # Motor de detección NER
│   │   ├── __init__.py
│   │   ├── engine.py             # Motor principal (Ollama/spaCy + regex)
│   │   ├── ollama_client.py      # Cliente HTTP para Ollama (LLM local)
│   │   └── patterns.py           # Patrones regex argentinos
│   ├── pdf/                      # Procesador de PDFs
│   │   ├── __init__.py
│   │   └── processor.py          # Extracción y redacción
│   ├── config/                   # Servicio de configuración
│   │   ├── __init__.py
│   │   └── service.py            # Persistencia de config
│   └── log/                      # Servicio de auditoría
│       ├── __init__.py
│       └── service.py            # Escritura/lectura de logs
├── frontend/                     # Frontend React + Cloudscape
│   ├── src/
│   │   ├── App.tsx               # Router principal
│   │   ├── main.tsx              # Entry point React
│   │   ├── pages/                # Páginas de la aplicación
│   │   │   ├── ProcessingPage.tsx
│   │   │   ├── ConfigPage.tsx
│   │   │   └── LogsPage.tsx
│   │   ├── components/           # Componentes reutilizables
│   │   │   ├── FolderInput.tsx
│   │   │   ├── FileList.tsx
│   │   │   ├── ProcessingProgress.tsx
│   │   │   ├── TypeToggle.tsx
│   │   │   └── LogTable.tsx
│   │   ├── services/             # Clientes de comunicación
│   │   │   ├── api.ts            # Cliente HTTP REST
│   │   │   └── sse.ts            # Cliente Server-Sent Events
│   │   ├── i18n/
│   │   │   └── es.ts            # Traducciones en español
│   │   └── types/
│   │       └── index.ts          # Tipos TypeScript
│   ├── package.json
│   ├── vite.config.ts
│   └── tsconfig.json
├── config/                       # Configuración persistente
│   ├── types_config.json         # Tipos de datos sensibles + prompt Ollama
│   ├── ollama.json               # Modelo, temperatura, keep_alive de Ollama
│   └── spacy.json                # Modelo spaCy configurado
├── models/                       # Modelo spaCy descargado
├── log/                          # Registros de auditoría (JSON Lines)
├── ofuscados/                    # Documentos ofuscados generados (PDF/MD/DOCX)
├── ofuscados_md/                 # Versiones Markdown de los ofuscados
├── test/                         # PDFs de ejemplo para pruebas
├── documentacion/                # Documentación del proyecto
│   ├── arquitectura.md           # Este documento
│   ├── guia_usuario.md           # Guía de uso
│   └── guia_instalacion.md       # Guía de instalación
├── scripts/                      # Scripts auxiliares
│   └── generate_test_pdfs.py     # Generador de PDFs de prueba
├── requirements.txt              # Dependencias Python
├── setup.sh                      # Instalador macOS
├── setup.bat                     # Instalador Windows
├── run.sh                        # Iniciar aplicación (macOS)
└── run.bat                       # Iniciar aplicación (Windows)
```

---

## Patrón de Comunicación

### REST (Frontend → Backend)

La comunicación principal entre el frontend y el backend se realiza mediante HTTP REST con payloads JSON.

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/folders/validate` | Valida ruta y lista archivos (PDF, MD, DOCX) |
| POST | `/api/folders/browse` | Navega directorios del sistema de archivos |
| POST | `/api/process` | Inicia procesamiento de ofuscación |
| POST | `/api/process/cancel` | Cancela el procesamiento en curso |
| GET | `/api/process/status` | Stream SSE de progreso |
| GET | `/api/config` | Obtiene configuración de tipos activos |
| PUT | `/api/config` | Actualiza configuración de tipos |
| GET / PUT | `/api/config/ollama` | Lee/guarda config de Ollama (modelo, temperatura, etc.) |
| GET / PUT | `/api/config/spacy` | Lee/guarda config de spaCy |
| GET | `/api/models/ollama` | Lista modelos de Ollama instalados |
| POST | `/api/models/ollama/pull` | Descarga un modelo de Ollama |
| GET | `/api/status/engine` | Estado de motores (Ollama/spaCy) y modelo activo |
| GET | `/api/logs` | Lista registros de auditoría (paginado) |
| GET | `/api/output/files` | Lista archivos ofuscados |
| GET | `/api/health` | Health check del servidor |

### SSE (Backend → Frontend)

Para las actualizaciones de progreso durante el procesamiento, el backend utiliza **Server-Sent Events (SSE)**, permitiendo al frontend recibir notificaciones en tiempo real sin necesidad de polling.

```
Frontend                          Backend
   │                                │
   │── POST /api/process ──────────▶│  (inicia procesamiento)
   │                                │
   │── GET /api/process/status ────▶│  (abre conexión SSE)
   │                                │
   │◀── event: progress ───────────│  (archivo 1 de N)
   │◀── event: progress ───────────│  (archivo 2 de N)
   │◀── event: progress ───────────│  (archivo 3 de N)
   │◀── event: complete ───────────│  (procesamiento finalizado)
   │                                │
```

### Despliegue Simplificado

FastAPI sirve los archivos estáticos del build de React directamente, eliminando la necesidad de un servidor web separado para el frontend y evitando problemas de CORS. Todo se accede desde un único puerto (3000 por defecto).
