# Flujo de la Aplicación DataMask

## Descripción General

DataMask procesa documentos (PDF, Markdown, Word) para detectar y enmascarar datos sensibles. A continuación se detalla el flujo completo de invocación entre los distintos componentes.

---

## Diagrama de Flujo Principal

```
┌─────────────────────────────────────────────────────────────────┐
│                     USUARIO (Navegador)                          │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                  FRONTEND (React + Cloudscape)                    │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Procesamiento│  │Configuración │  │ Archivos Ofuscados   │  │
│  │              │  │              │  │                      │  │
│  │ 1. Explorar  │  │ • Toggles    │  │ • Listar PDFs/MD     │  │
│  │ 2. Validar   │  │ • Editar desc│  │ • Ver contenido      │  │
│  │ 3. Seleccionar│ │ • Agregar    │  │ • Borrar individual  │  │
│  │ 4. Procesar  │  │   tipos      │  │ • Borrar todos       │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘  │
│         │                  │                      │              │
│  ┌──────┴──────┐  ┌───────┴───────┐  ┌──────────┴──────────┐  │
│  │  Logs       │  │    Ayuda      │  │   Documentación      │  │
│  │  • Historial│  │ • Instrucciones│ │   • Arquitectura     │  │
│  │  • Paginado │  │ • Formatos    │  │   • Guía usuario     │  │
│  │             │  │ • Seguridad   │  │   • Guía instalación │  │
│  └─────────────┘  └───────────────┘  │   • Flujo app        │  │
│                                       │   • Security         │  │
│                                       └──────────────────────┘  │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTP REST + SSE
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                   BACKEND (FastAPI)                               │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    API Routes                            │    │
│  │                                                         │    │
│  │  POST /api/folders/validate  → File Service             │    │
│  │  POST /api/folders/browse    → File System              │    │
│  │  POST /api/process           → Processing Pipeline      │    │
│  │  GET  /api/process/status    → SSE Events               │    │
│  │  GET  /api/config            → Config Service           │    │
│  │  PUT  /api/config            → Config Service           │    │
│  │  GET  /api/logs              → Log Service              │    │
│  │  GET  /api/output/files      → File System              │    │
│  │  POST /api/output/delete     → File System              │    │
│  │  GET  /api/output/view/...   → File Response            │    │
│  │  GET  /api/docs/list         → Documentación            │    │
│  │  GET  /api/docs/view/...     → Documentación            │    │
│  └─────────────────────────────────────────────────────────┘    │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                 SERVICIOS INTERNOS                                │
│                                                                   │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────────┐  │
│  │  NER Engine    │  │ PDF Processor  │  │  Config Service  │  │
│  │                │  │                │  │                  │  │
│  │ • Ollama (LLM)│  │ • PDF (fitz)   │  │ • Load JSON      │  │
│  │ • spaCy NER   │  │ • Markdown     │  │ • Save JSON      │  │
│  │   (fallback)  │  │ • Word (docx)  │  │ • Validate       │  │
│  │ • Regex AR    │  │ • Redacciones  │  │                  │  │
│  │ • Filtrado    │  │                │  │                  │  │
│  │ • Conflictos  │  │                │  │                  │  │
│  └───────┬────────┘  └───────┬────────┘  └──────────────────┘  │
│          │                   │                                   │
│          │                   ▼                                   │
│          │           ┌────────────────┐  ┌──────────────────┐  │
│          │           │  Log Service   │  │  File Service    │  │
│          │           │                │  │                  │  │
│          │           │ • Write JSONL  │  │ • Validate path  │  │
│          │           │ • Read paged   │  │ • List documents │  │
│          │           │ • OS user      │  │ • OS detection   │  │
│          │           └────────────────┘  └──────────────────┘  │
│          │                                                       │
│          ▼                                                       │
│  ┌────────────────────────────────────────────────────────┐     │
│  │              MODELO IA LOCAL                            │     │
│  │   Ollama (modelo configurable, ej: llama3.1:8b)        │     │
│  │   o spaCy es_core_news_lg (~560MB, fallback)           │     │
│  │              • Nombres → [NOMBRE]                       │     │
│  │              • Direcciones → [DIRECCION]                │     │
│  └────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                   SISTEMA DE ARCHIVOS                             │
│                                                                   │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────┐ │
│  │ofuscados/│  │ofuscados_md/ │  │    log/      │  │config/ │ │
│  │ *.pdf    │  │ *.md         │  │ audit.jsonl  │  │types_  │ │
│  │ *.docx   │  │              │  │              │  │config  │ │
│  │ *.md     │  │              │  │              │  │.json   │ │
│  └──────────┘  └──────────────┘  └──────────────┘  └────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## Flujo Detallado: Procesamiento de Documentos

### Paso 1: Selección de carpeta

```
Usuario → [Explorar] → POST /api/folders/browse
                        ← Lista de directorios y archivos
Usuario → [Seleccionar carpeta]
Usuario → [Validar]  → POST /api/folders/validate
                        → file_service.validate_path()
                          • Verifica existencia
                          • Verifica es directorio
                          • Verifica permisos lectura
                          • Verifica longitud de ruta
                        → file_service.list_document_files()
                          • Busca *.pdf, *.md, *.docx
                          • Case-insensitive
                        ← Lista de FileInfo (nombre, tamaño, ruta)
```

### Paso 2: Selección de archivos

```
Frontend muestra tabla con checkboxes
Usuario → [Seleccionar todo] o selección individual
Usuario → [Iniciar procesamiento]
```

### Paso 3: Inicio del procesamiento

```
Frontend → POST /api/process {folder_path, selected_files}
Backend:
  1. Valida carpeta (validate_and_list_documents)
  2. Filtra por selected_files (si se proporcionaron)
  3. Verifica que no hay procesamiento activo
  4. Crea asyncio.Queue para eventos SSE
  5. Lanza asyncio.create_task(_process_files)
  ← {message: "Procesamiento iniciado", total_files: N}

Frontend → GET /api/process/status (EventSource SSE)
```

### Paso 4: Procesamiento en background (por cada archivo)

```
_process_files():
  1. Carga ConfigService → TypeConfig
  2. Obtiene NEREngine singleton (pre-cargado)
  3. Actualiza config del NER
  4. Crea PDFProcessor(output_dir, ner_engine)

  Para cada archivo:
    ├── Emite SSE: event: file_start
    │
    ├── Despacha según extensión:
    │   ├── .pdf  → _process_pdf_file()
    │   ├── .md   → _process_markdown_file()
    │   └── .docx → _process_docx_file()
    │
    ├── Registra en LogService (audit.jsonl)
    │
    └── Emite SSE: event: file_complete | file_error

  Al finalizar:
    └── Emite SSE: event: complete {total, success, failed}
```

### Paso 5: Procesamiento de un PDF

```
_process_pdf_file(file_path):
  1. Abre PDF con fitz.open()
     • Si está encriptado → PDFProcessingError
     • Si está corrupto → PDFProcessingError

  2. Primera pasada (solo lectura):
     Para cada página:
       • Extrae texto con page.get_text()
       • Detecta entidades con NEREngine.detect(text, page_num)
         ├── Ollama: nombres y direcciones (o spaCy como fallback)
         ├── Regex: DNI, CUIT, email, teléfono, celular, etc.
         ├── Filtra por confianza >= 0.70
         ├── Filtra por tipos activos en config
         └── Resuelve conflictos (mayor confianza gana)

  3. Si no hay entidades → retorna success con 0 entidades

  4. Copia archivo original → ofuscados/{nombre}_ofuscado.pdf

  5. Abre la copia y aplica redacciones:
     Para cada página:
       • Busca texto de cada entidad con page.search_for()
       • Detecta font/tamaño del texto original
       • Agrega redacción: page.add_redact_annot(rect, text="[TIPO]")
       • Aplica: page.apply_redactions()

  6. Guarda con doc.saveIncr() (preserva estructura)

  7. Genera versión Markdown → ofuscados_md/{nombre}_ofuscado.md

  8. Retorna ProcessingResult
```

### Paso 6: Procesamiento de un Markdown

```
_process_markdown_file(file_path):
  1. Lee texto completo del archivo
  2. Detecta entidades con NEREngine.detect(text, page=0)
  3. Aplica redacciones de texto (de atrás hacia adelante)
  4. Guarda en ofuscados/{nombre}_ofuscado.md
  5. Genera copia en ofuscados_md/{nombre}_ofuscado.md
  6. Retorna ProcessingResult
```

### Paso 7: Procesamiento de un Word

```
_process_docx_file(file_path):
  1. Abre con python-docx Document()
  2. Extrae texto de todos los párrafos
  3. Detecta entidades en el texto completo
  4. Para cada párrafo con entidades:
     • Detecta entidades del párrafo
     • Aplica redacciones al texto
     • Reemplaza runs del párrafo
  5. Guarda en ofuscados/{nombre}_ofuscado.docx
  6. Genera versión Markdown en ofuscados_md/
  7. Retorna ProcessingResult
```

---

## Flujo: Configuración de Tipos

```
Frontend (ConfigPage):
  1. GET /api/config → carga config actual (v2 con descripciones)
  2. Usuario modifica toggles / edita descripciones / agrega tipos
  3. PUT /api/config → valida (min 1 activo) → guarda JSON
  4. Próximo procesamiento usa la config actualizada
```

---

## Flujo: Gestión de Archivos Ofuscados

```
Frontend (OutputPage):
  1. GET /api/output/files?folder=all → lista PDFs + Markdown
  2. Usuario selecciona archivos
  3. Click en nombre → GET /api/output/view/{folder}/{filename}
     • PDF → se abre en visor del navegador
     • MD → se muestra como texto
     • DOCX → se descarga
  4. [Eliminar seleccionados] → POST /api/output/delete
  5. [Eliminar todos] → POST /api/output/delete-all?folder=...
```

---

## Flujo: Registro de Auditoría

```
Escritura (automática durante procesamiento):
  LogService.write_entry():
    • filename, file_size_bytes (volumen del documento)
    • os_user (detectado del OS)
    • timestamp (ISO 8601 con timezone)
    • result (success/error)
    • entities_detected, entities_by_type
    • engine (motor y modelo usado, ej: "ollama (llama3.1:8b)" o "spacy")
    • processing_time_ms (tiempo de procesamiento del archivo)
    • error_detail (mensaje de error si el archivo falló)

Lectura (desde la UI):
  GET /api/logs?page=1&page_size=100
    → LogService.read_entries()
    → Lee audit.jsonl línea por línea
    → Ordena de más reciente a más antiguo
    → Aplica paginación

La tabla de logs muestra además el detalle del error (popover "Ver error")
y el tiempo de procesamiento por archivo.
```

---

## Comunicación Frontend ↔ Backend

| Tipo | Uso | Protocolo |
|------|-----|-----------|
| Operaciones CRUD | Validar, config, logs, borrar | HTTP REST (JSON) |
| Progreso en tiempo real | Durante procesamiento | Server-Sent Events (SSE) |
| Archivos estáticos | Frontend React build | Servidos por FastAPI |
| Documentos ofuscados | Ver contenido | FileResponse / PlainTextResponse |

---

## Ciclo de Vida del Motor NER

```
1. Primera invocación de _get_ner_engine():
   • Detecta si Ollama está disponible (localhost:11434)
   • Si Ollama está disponible: lo usa como motor primario
   • Si no: carga spaCy es_core_news_lg (~3 segundos) como fallback
   • Crea instancia singleton de NEREngine
   • Se mantiene en memoria durante toda la sesión

2. Cada procesamiento:
   • Recarga la config y los patrones regex desde types_config.json
   • Lee el modelo de Ollama configurado desde ollama.json
   • Actualiza config del singleton (ner_engine.config = config)
   • Recalcula tipos activos
   • Reutiliza el motor ya cargado

NOTA: el singleton se mantiene en memoria entre requests. Tras cambios
en el código o en los archivos de config, reiniciar la app para garantizar
que el motor se recree limpio (ver .kiro/steering/dev-workflow.md).
```
