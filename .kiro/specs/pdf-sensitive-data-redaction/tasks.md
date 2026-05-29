# Implementation Plan: PDF Sensitive Data Redaction

## Overview

Implementación de una aplicación web local para ofuscación de datos sensibles en PDFs. El backend en Python (FastAPI) maneja la detección NER con spaCy y patrones regex argentinos, mientras el frontend React + Cloudscape provee la interfaz en español. La arquitectura sigue un patrón cliente-servidor con comunicación REST y SSE para progreso en tiempo real.

## Tasks

- [x] 1. Estructura del proyecto y configuración base
  - [x] 1.1 Crear estructura de directorios y archivos de configuración del proyecto
    - Crear la estructura de carpetas: `app/`, `app/api/`, `app/ner/`, `app/pdf/`, `app/config/`, `app/log/`, `frontend/`, `models/`, `config/`, `log/`, `ofuscados/`, `test/`, `documentacion/`
    - Crear `requirements.txt` con dependencias: fastapi, uvicorn, pymupdf, spacy, pydantic, python-multipart, httpx
    - Crear archivos `__init__.py` en todos los paquetes Python
    - Crear `config/types_config.json` con configuración por defecto (todos los tipos activos)
    - _Requirements: 1.1, 10.1, 10.2, 10.3_

  - [x] 1.2 Implementar modelos de datos base y excepciones
    - Crear `app/models.py` con dataclasses/Pydantic: `TypeConfig`, `FileInfo`, `DetectedEntity`, `ProcessingResult`, `AuditLogEntry`
    - Crear `app/exceptions.py` con jerarquía de errores: `AppError`, `PathValidationError`, `PDFProcessingError`, `ConfigError`
    - Definir `SensitiveDataType` como Enum con los 10 tipos
    - _Requirements: 3.2, 4.1, 5.2, 8.1_

  - [x] 1.3 Implementar entry point de FastAPI con creación automática de carpetas
    - Crear `app/main.py` con la app FastAPI, middleware CORS, y evento startup que cree carpetas faltantes (`log/`, `ofuscados/`, `test/`, `documentacion/`)
    - Configurar servicio de archivos estáticos para servir el build de React
    - Implementar endpoint `/api/health` para health check
    - Mostrar URL de acceso en terminal al iniciar
    - _Requirements: 1.1, 1.4, 1.5, 1.6, 10.3, 11.7, 12.6_

- [x] 2. Servicio de configuración
  - [x] 2.1 Implementar ConfigService con persistencia JSON
    - Crear `app/config/service.py` con métodos `load()`, `save()`, `validate()`
    - Implementar carga desde `config/types_config.json` con fallback a defaults si el archivo no existe o está corrupto
    - Implementar validación de que al menos un tipo esté activo
    - Incluir campo `version` y `updated_at` en el JSON persistido
    - _Requirements: 4.1, 4.2, 4.5, 4.6, 4.7_

  - [ ]* 2.2 Write property test: Configuration persistence round-trip
    - **Property 8: Configuration persistence round-trip**
    - Para cualquier `TypeConfig` válido, guardar y cargar debe producir configuración equivalente
    - **Validates: Requirements 4.5**

  - [ ]* 2.3 Write property test: Corrupted configuration fallback
    - **Property 9: Corrupted configuration fallback**
    - Para cualquier JSON inválido o corrupto, el loader debe retornar configuración por defecto con todos los tipos activos
    - **Validates: Requirements 4.6**

  - [ ]* 2.4 Write property test: Minimum one active type validation
    - **Property 10: Minimum one active type validation**
    - Para cualquier configuración con todos los tipos inactivos, la validación debe rechazarla
    - **Validates: Requirements 4.7**

- [x] 3. Validación de rutas y listado de archivos
  - [x] 3.1 Implementar File Service con validación de rutas
    - Crear `app/api/file_service.py` con validación de ruta (existencia, es directorio, permisos de lectura)
    - Implementar clasificación de errores: NOT_FOUND, NOT_DIR, NO_PERMISSION
    - Validar longitud de ruta según OS (260 Windows, 1024 macOS)
    - Implementar detección automática de OS para separadores de ruta
    - _Requirements: 2.1, 2.3, 9.3, 9.4, 9.5_

  - [x] 3.2 Implementar listado de archivos PDF case-insensitive
    - Listar archivos con extensión `.pdf` (case-insensitive) en el nivel superior de la carpeta
    - Retornar nombre y tamaño en bytes de cada archivo
    - Manejar rutas con espacios, caracteres acentuados y separadores nativos del OS
    - _Requirements: 2.2, 2.4, 9.3_

  - [ ]* 3.3 Write property test: Path length validation
    - **Property 1: Path length validation**
    - Validar que rutas ≤ 260 (Windows) o ≤ 1024 (macOS) son aceptadas y las que exceden son rechazadas
    - **Validates: Requirements 2.1, 9.5**

  - [ ]* 3.4 Write property test: PDF file listing is case-insensitive
    - **Property 2: PDF file listing is case-insensitive**
    - Para cualquier directorio con archivos .pdf/.PDF/.Pdf, todos deben ser listados
    - **Validates: Requirements 2.2, 2.4**

  - [ ]* 3.5 Write property test: Path error classification
    - **Property 3: Path error classification**
    - Para cualquier ruta inválida, el error debe clasificarse correctamente según la causa
    - **Validates: Requirements 2.3**

  - [ ]* 3.6 Write property test: Path handling with special characters
    - **Property 16: Path handling with special characters**
    - Para rutas con espacios, acentos y separadores nativos, las operaciones deben completarse sin errores
    - **Validates: Requirements 9.3**

- [x] 4. Motor NER con spaCy y regex
  - [x] 4.1 Implementar patrones regex para formatos argentinos
    - Crear `app/ner/patterns.py` con regex para: DNI, CUIT/CUIL, teléfono +54, celular, email, tarjeta de crédito, pasaporte AR, cuenta bancaria
    - Cada patrón debe retornar `DetectedEntity` con tipo, posición, confianza y página
    - Implementar confianza fija de 0.95 para matches regex exactos
    - _Requirements: 3.2, 3.3_

  - [x] 4.2 Implementar NEREngine con integración spaCy
    - Crear `app/ner/engine.py` con clase `NEREngine`
    - Cargar modelo `es_core_news_lg` para detección de PER (nombres) y LOC (direcciones)
    - Combinar resultados de spaCy con resultados de regex
    - Implementar filtrado por umbral de confianza ≥ 0.70
    - Implementar resolución de conflictos por mayor confianza
    - Respetar configuración de tipos activos/inactivos
    - _Requirements: 3.1, 3.4, 3.5, 3.6, 4.3, 4.4, 6.2_

  - [ ]* 4.3 Write property test: Argentine format regex detection
    - **Property 4: Argentine format regex detection**
    - Para cualquier dato sensible válido en formato argentino, el regex debe detectarlo y clasificarlo correctamente
    - **Validates: Requirements 3.2, 3.3**

  - [ ]* 4.4 Write property test: Confidence threshold filtering
    - **Property 5: Confidence threshold filtering**
    - Para cualquier entidad detectada, debe incluirse si y solo si su confianza es ≥ 0.70
    - **Validates: Requirements 3.4**

  - [ ]* 4.5 Write property test: Conflict resolution by highest confidence
    - **Property 6: Conflict resolution by highest confidence**
    - Para cualquier span que coincida con múltiples tipos, se asigna el de mayor confianza
    - **Validates: Requirements 3.6**

  - [ ]* 4.6 Write property test: Detection respects type configuration
    - **Property 7: Detection respects type configuration**
    - Para cualquier configuración de tipos, solo se detectan entidades de tipos activos
    - **Validates: Requirements 4.3, 4.4**

- [x] 5. Checkpoint - Verificar motor NER y configuración
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Procesador de PDFs
  - [x] 6.1 Implementar PDFProcessor con PyMuPDF
    - Crear `app/pdf/processor.py` con clase `PDFProcessor`
    - Implementar extracción de texto por página con `fitz`
    - Implementar aplicación de redacciones usando el mecanismo nativo de PyMuPDF (`add_redact_annot` + `apply_redactions`)
    - Reemplazar cada dato sensible con su etiqueta `[TIPO]` correspondiente
    - Manejar PDFs corruptos o protegidos con contraseña (log error, skip, continuar)
    - _Requirements: 5.1, 5.3, 5.4, 5.6_

  - [x] 6.2 Implementar generación de archivos de salida
    - Generar ruta de salida con sufijo `_ofuscado` antes de la extensión en carpeta `ofuscados/`
    - Preservar archivo original sin modificaciones
    - Retornar `ProcessingResult` con estadísticas de entidades por tipo
    - _Requirements: 5.5, 10.4, 10.5_

  - [ ]* 6.3 Write property test: Redaction replaces with correct label
    - **Property 11: Redaction replaces with correct label**
    - Para cualquier texto con datos sensibles, la redacción debe reemplazar con `[TIPO]` y el texto original no debe estar presente
    - **Validates: Requirements 5.1, 5.6**

  - [ ]* 6.4 Write property test: PDF structure preservation
    - **Property 12: PDF structure preservation**
    - Para cualquier PDF procesado, el output debe tener el mismo número de páginas y el texto no sensible debe permanecer igual
    - **Validates: Requirements 5.3**

  - [ ]* 6.5 Write property test: Output filename generation
    - **Property 13: Output filename generation**
    - Para cualquier nombre de archivo, la salida debe tener sufijo `_ofuscado` antes de `.pdf` en `ofuscados/`
    - **Validates: Requirements 5.5, 10.5**

  - [ ]* 6.6 Write property test: Original file integrity
    - **Property 17: Original file integrity**
    - Para cualquier PDF procesado, el archivo original debe permanecer byte-for-byte idéntico
    - **Validates: Requirements 10.4**

- [x] 7. Servicio de logging
  - [x] 7.1 Implementar LogService con formato JSON Lines
    - Crear `app/log/service.py` con clase `LogService`
    - Implementar `write_entry()` que escribe una línea JSON por entrada en `log/`
    - Implementar `read_entries()` con paginación (máximo 100 por página) ordenados de más reciente a más antiguo
    - Registrar: filename, file_size_bytes, os_user, timestamp ISO 8601 con timezone, result, entities_detected, entities_by_type
    - Manejar error de escritura sin interrumpir procesamiento
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

  - [ ]* 7.2 Write property test: Audit log entry round-trip
    - **Property 14: Audit log entry round-trip**
    - Para cualquier `AuditLogEntry` válido, escribir y leer debe producir entrada equivalente
    - **Validates: Requirements 8.1, 8.2, 8.4**

  - [ ]* 7.3 Write property test: Log ordering and pagination
    - **Property 15: Log ordering and pagination**
    - Para cualquier conjunto de entradas con timestamps distintos, deben retornarse en orden descendente con máximo 100 por página
    - **Validates: Requirements 8.3**

- [x] 8. API REST endpoints
  - [x] 8.1 Implementar endpoints de validación de carpeta y configuración
    - Crear `app/api/routes.py` con router FastAPI
    - `POST /api/folders/validate`: valida ruta y lista PDFs
    - `GET /api/config`: retorna configuración actual
    - `PUT /api/config`: actualiza configuración con validación
    - Manejar errores con HTTP 422 (validación) y 404 (no encontrado)
    - _Requirements: 2.1, 2.2, 2.3, 4.1, 4.5, 4.7_

  - [x] 8.2 Implementar endpoint de procesamiento con SSE
    - `POST /api/process`: inicia procesamiento de PDFs en la carpeta indicada
    - `GET /api/process/status`: Server-Sent Events stream para progreso en tiempo real
    - Procesar archivos en cola, reportar progreso por archivo
    - Si un archivo falla, registrar error, notificar vía SSE, continuar con el siguiente
    - Al finalizar, enviar resumen con archivos exitosos y fallidos
    - _Requirements: 3.5, 5.4_

  - [x] 8.3 Implementar endpoint de logs
    - `GET /api/logs`: retorna registros de auditoría paginados
    - Parámetros: `page` (default 1), `page_size` (default 100)
    - Ordenados de más reciente a más antiguo
    - _Requirements: 8.3_

- [x] 9. Checkpoint - Verificar backend completo
  - Ensure all tests pass, ask the user if questions arise.

- [x] 10. Frontend React con Cloudscape
  - [x] 10.1 Inicializar proyecto React con Cloudscape y estructura base
    - Crear proyecto React con TypeScript en `frontend/`
    - Instalar dependencias: `@cloudscape-design/components`, `@cloudscape-design/global-styles`
    - Crear estructura: `pages/`, `components/`, `services/`, `i18n/`, `types/`
    - Configurar `i18n/es.ts` con todas las traducciones en español
    - Crear tipos TypeScript compartidos en `types/index.ts`
    - _Requirements: 1.2, 1.3_

  - [x] 10.2 Implementar página de procesamiento con selector de carpeta y progreso
    - Crear `ProcessingPage.tsx` como página principal
    - Implementar `FolderInput.tsx` con campo de texto y botón de validación
    - Implementar `FileList.tsx` para mostrar PDFs encontrados (nombre y tamaño)
    - Implementar `ProcessingProgress.tsx` con barra de progreso conectada a SSE
    - Mostrar resumen de resultados al finalizar
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 3.5_

  - [x] 10.3 Implementar página de configuración de tipos
    - Crear `ConfigPage.tsx` con toggles para cada tipo de dato sensible
    - Implementar `TypeToggle.tsx` como componente individual
    - Conectar con `PUT /api/config` para persistir cambios
    - Validar que al menos un tipo permanezca activo (mostrar error si se intenta desactivar todos)
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.7_

  - [x] 10.4 Implementar página de visor de logs
    - Crear `LogsPage.tsx` con tabla de registros de auditoría
    - Implementar `LogTable.tsx` con columnas: archivo, tamaño, usuario, fecha, resultado, entidades
    - Implementar paginación con máximo 100 registros por página
    - Ordenar de más reciente a más antiguo
    - _Requirements: 8.3_

  - [x] 10.5 Implementar servicios de comunicación con backend
    - Crear `services/api.ts` con cliente HTTP para todos los endpoints
    - Crear `services/sse.ts` con cliente SSE para progreso en tiempo real
    - Manejar errores de red y mostrar mensajes en español
    - _Requirements: 1.4, 8.5_

- [x] 11. Instaladores multiplataforma
  - [x] 11.1 Crear setup.sh para macOS
    - Verificar prerequisitos: versión de Python ≥ 3.9, espacio en disco, permisos de escritura
    - Crear entorno virtual e instalar dependencias Python
    - Descargar modelo spaCy `es_core_news_lg` con verificación de integridad
    - Instalar dependencias del frontend (npm install) y generar build
    - Crear estructura de carpetas del proyecto
    - Mostrar mensaje de éxito o error con instrucciones de resolución
    - _Requirements: 6.1, 6.3, 6.4, 6.5, 7.1, 7.3, 7.4, 7.5, 7.6_

  - [x] 11.2 Crear setup.bat para Windows
    - Verificar prerequisitos: versión de Python ≥ 3.9, espacio en disco, permisos de escritura
    - Crear entorno virtual e instalar dependencias Python
    - Descargar modelo spaCy `es_core_news_lg` con verificación de integridad
    - Instalar dependencias del frontend (npm install) y generar build
    - Crear estructura de carpetas del proyecto
    - Mostrar mensaje de éxito o error con instrucciones de resolución
    - _Requirements: 6.1, 6.3, 6.4, 6.5, 7.2, 7.3, 7.4, 7.5, 7.6_

- [x] 12. PDFs de ejemplo y documentación
  - [x] 12.1 Crear PDFs de ejemplo en carpeta test/
    - Generar 3 PDFs con datos sensibles ficticios argentinos usando reportlab o similar
    - PDF 1: Formulario de registro (nombre, DNI, email, teléfono, dirección)
    - PDF 2: Contrato de servicio (nombre, CUIT/CUIL, dirección, cuenta bancaria)
    - PDF 3: Ficha de empleado (nombre, DNI, email, celular, pasaporte, tarjeta de crédito)
    - Usar exclusivamente datos ficticios que no correspondan a personas reales
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6_

  - [x] 12.2 Crear documentación del proyecto en carpeta documentacion/
    - Crear `documentacion/arquitectura.md`: componentes, tecnologías, flujo de procesamiento, diagrama de carpetas
    - Crear `documentacion/guia_usuario.md`: iniciar app, seleccionar carpeta, configurar tipos, ejecutar ofuscación, consultar logs
    - Crear `documentacion/guia_instalacion.md`: prerequisitos, pasos de instalación macOS/Windows, verificación, resolución de problemas
    - Toda la documentación en español con terminología del glosario de requirements
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.7_

- [x] 13. Integración final y wiring
  - [x] 13.1 Integrar frontend build con FastAPI y configurar servicio de archivos estáticos
    - Configurar FastAPI para servir el build de React desde `frontend/build/`
    - Eliminar necesidad de CORS en producción (mismo origen)
    - Verificar que la app completa funciona desde un solo comando `uvicorn app.main:app`
    - Crear script `run.sh` / `run.bat` para iniciar la aplicación
    - _Requirements: 1.1, 1.4, 1.6_

  - [ ]* 13.2 Write integration tests para pipeline completo
    - Test end-to-end: procesar carpeta test/ con 3 PDFs
    - Verificar archivos generados en `ofuscados/` con sufijo correcto
    - Verificar entradas en `log/` con formato correcto
    - Verificar que originales no se modifican
    - _Requirements: 11.6, 10.4, 10.5, 8.1_

- [x] 14. Checkpoint final - Verificar aplicación completa
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document (17 properties)
- Unit tests validate specific examples and edge cases
- El backend usa Python con FastAPI, pytest y hypothesis para testing
- El frontend usa React + TypeScript con Cloudscape Design System
- Toda la UI y documentación debe estar en español
- Los patrones regex están optimizados para formatos argentinos

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2", "1.3"] },
    { "id": 2, "tasks": ["2.1", "3.1", "3.2"] },
    { "id": 3, "tasks": ["2.2", "2.3", "2.4", "3.3", "3.4", "3.5", "3.6", "4.1"] },
    { "id": 4, "tasks": ["4.2"] },
    { "id": 5, "tasks": ["4.3", "4.4", "4.5", "4.6", "6.1", "7.1"] },
    { "id": 6, "tasks": ["6.2", "7.2", "7.3"] },
    { "id": 7, "tasks": ["6.3", "6.4", "6.5", "6.6", "8.1", "8.3"] },
    { "id": 8, "tasks": ["8.2"] },
    { "id": 9, "tasks": ["10.1", "11.1", "11.2", "12.1", "12.2"] },
    { "id": 10, "tasks": ["10.2", "10.3", "10.4", "10.5"] },
    { "id": 11, "tasks": ["13.1"] },
    { "id": 12, "tasks": ["13.2"] }
  ]
}
```
