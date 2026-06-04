# Security Assessment Report — DataMask v1.0

**Fecha:** 2025-01-XX  
**Aplicación:** DataMask — Enmascaramiento de datos sensibles en PDFs  
**Alcance:** Revisión completa del código fuente (backend Python + frontend React)  
**Evaluador:** Kiro Security Assessment  

---

## Resumen Ejecutivo

| Severidad | Hallazgos |
|-----------|-----------|
| CRITICAL  | 1         |
| HIGH      | 3         |
| MEDIUM    | 5         |
| LOW       | 4         |
| INFO      | 4         |

La aplicación DataMask es una herramienta local (desktop) para ofuscación de datos sensibles.
Su superficie de ataque principal es la exposición de red y el acceso al sistema de archivos.
Los hallazgos más críticos se relacionan con la falta de restricciones en el acceso al
sistema de archivos y la configuración de red del servidor.

---

## 1. Path Traversal Vulnerabilities

### FINDING-01: Navegación de directorios sin restricciones (browse_folders)

- **Severidad:** HIGH
- **Archivo:** `app/api/routes.py` — endpoint `POST /api/folders/browse`
- **Líneas:** ~290-330
- **Descripción:** El endpoint `browse_folders` permite navegar cualquier directorio del sistema de archivos sin restricción alguna. Un atacante con acceso a la red puede explorar `/etc/`, `/root/`, `/var/`, o cualquier directorio sensible del sistema operativo.
- **Impacto:** Enumeración completa del sistema de archivos, descubrimiento de archivos sensibles, rutas de configuración, y estructura del servidor.
- **Fix recomendado:**
  - Implementar una lista blanca de directorios base permitidos (ej: solo el home del usuario o directorios configurados).
  - Alternativamente, restringir la navegación a un directorio raíz configurable y validar que todas las rutas resueltas estén dentro de ese directorio usando `Path.resolve().relative_to()`.

### FINDING-02: Validación de carpetas permite acceso a cualquier directorio

- **Severidad:** HIGH
- **Archivo:** `app/api/file_service.py` — función `validate_path()`
- **Líneas:** ~60-110
- **Descripción:** La función `validate_path()` acepta cualquier ruta absoluta del sistema y solo verifica existencia, tipo (directorio) y permisos de lectura. No hay restricción sobre qué directorios son accesibles. Un usuario puede apuntar a `/etc/`, `/var/log/`, o cualquier directorio con archivos `.md` o `.pdf`.
- **Impacto:** Lectura de archivos PDF/MD/DOCX de cualquier ubicación del sistema.
- **Fix recomendado:**
  - Definir un conjunto de directorios base permitidos en la configuración.
  - Validar que la ruta proporcionada esté dentro de los directorios permitidos.

### FINDING-03: Endpoint output/view con protección parcial de path traversal

- **Severidad:** MEDIUM
- **Archivo:** `app/api/routes.py` — endpoint `GET /api/output/view/{folder}/{filename}`
- **Líneas:** ~380-415
- **Descripción:** El endpoint implementa correctamente una verificación de path traversal usando `file_path.resolve().relative_to()`, lo cual es positivo. Sin embargo, el parámetro `folder` solo se valida contra una lista fija (`ofuscados`, `ofuscados_md`), lo cual es correcto. La protección es adecuada para este endpoint.
- **Estado:** ✅ Protegido correctamente.

### FINDING-04: Endpoint output/delete con protección de path traversal

- **Severidad:** LOW
- **Archivo:** `app/api/routes.py` — endpoint `POST /api/output/delete`
- **Líneas:** ~345-375
- **Descripción:** El endpoint de borrado implementa correctamente `file_path.resolve().relative_to(folder_path.resolve())` para prevenir path traversal. Sin embargo, el parámetro `folder` en el body del request no está validado contra la lista permitida (solo se valida en `delete-all`). Un atacante podría enviar `folder: "../../"` para intentar borrar archivos fuera de las carpetas esperadas.
- **Impacto:** Potencial borrado de archivos fuera de `ofuscados/` si se manipula el campo `folder`.
- **Fix recomendado:**
  - Agregar validación explícita de `request.folder` contra `("ofuscados", "ofuscados_md")` al inicio del endpoint `delete`, igual que se hace en `delete-all`.

---

## 2. Input Validation

### FINDING-05: Falta de sanitización en el campo `path` de FolderValidationRequest

- **Severidad:** MEDIUM
- **Archivo:** `app/api/routes.py` — modelo `FolderValidationRequest`
- **Descripción:** El campo `path` es un `str` sin validación de longitud máxima a nivel de Pydantic (aunque `file_service.py` valida longitud según OS). No hay sanitización de caracteres nulos (`\x00`), secuencias de escape, o caracteres de control que podrían causar comportamiento inesperado en el sistema de archivos.
- **Fix recomendado:**
  - Agregar `max_length` al campo path en el modelo Pydantic.
  - Rechazar rutas que contengan caracteres nulos (`\x00`) o caracteres de control.
  - Ejemplo: `path: str = Field(max_length=4096, pattern=r'^[^\x00]+$')`

### FINDING-06: Custom regex patterns sin validación (ReDoS potencial)

- **Severidad:** MEDIUM
- **Archivo:** `frontend/src/pages/ConfigPage.tsx` — campo `pattern` en tipos custom
- **Descripción:** La UI permite al usuario definir patrones regex personalizados para tipos de datos custom. Si estos patrones se compilan y ejecutan en el backend sin validación, un patrón malicioso podría causar ReDoS (Regular Expression Denial of Service). Actualmente el backend no parece usar los custom patterns en el procesamiento NER, pero la infraestructura está preparada para ello.
- **Impacto:** Si se implementa la ejecución de custom patterns, un regex como `(a+)+$` contra un input largo podría bloquear el procesamiento.
- **Fix recomendado:**
  - Validar la complejidad del regex antes de aceptarlo (limitar longitud, prohibir backreferences anidadas).
  - Usar `re.compile()` con timeout o la librería `regex` con flag `TIMEOUT`.
  - Ejecutar regex en un thread con timeout.

### FINDING-07: Endpoint update_config acepta JSON arbitrario

- **Severidad:** LOW
- **Archivo:** `app/api/routes.py` — endpoint `PUT /api/config`
- **Líneas:** ~140-180
- **Descripción:** El endpoint usa `await request.json()` directamente sin un modelo Pydantic tipado, aceptando cualquier estructura JSON. Aunque se valida que al menos un tipo esté activo, no se valida la estructura completa del payload, permitiendo inyección de campos arbitrarios en el archivo de configuración.
- **Fix recomendado:**
  - Definir un modelo Pydantic estricto para el request body de configuración.
  - Usar `model_validate()` para rechazar campos no esperados.

---

## 3. File System Access

### FINDING-08: Procesamiento de archivos de cualquier ubicación del sistema

- **Severidad:** CRITICAL
- **Archivo:** `app/api/routes.py` — endpoint `POST /api/process`
- **Descripción:** El endpoint de procesamiento acepta cualquier `folder_path` y procesa todos los archivos PDF/MD/DOCX encontrados. Combinado con la falta de restricción de directorios (FINDING-02), esto permite:
  1. Leer el contenido de cualquier PDF/MD/DOCX del sistema.
  2. Escribir archivos en la carpeta `ofuscados/` con el contenido procesado.
  3. El log de auditoría registra los nombres de archivos procesados, exponiendo rutas del sistema.
- **Impacto:** Exfiltración de datos de documentos sensibles de cualquier ubicación del sistema de archivos. Un atacante con acceso a la red podría procesar documentos confidenciales y luego descargar las versiones "ofuscadas" (que aún contienen la mayor parte del contenido original).
- **Fix recomendado:**
  - Restringir `folder_path` a directorios dentro de una lista blanca configurable.
  - Implementar un directorio "workspace" configurable como raíz de operaciones.
  - Considerar que los archivos ofuscados aún contienen contenido parcial del original.

### FINDING-09: serve_spa puede servir archivos arbitrarios del directorio frontend

- **Severidad:** LOW
- **Archivo:** `app/main.py` — función `serve_spa()`
- **Líneas:** ~115-120
- **Descripción:** La función `serve_spa` intenta servir archivos estáticos del directorio frontend build. Verifica `file_path.is_file()` pero no valida path traversal. Sin embargo, FastAPI/Starlette normaliza las rutas antes de pasarlas al handler, mitigando parcialmente el riesgo.
- **Fix recomendado:**
  - Agregar validación explícita: `file_path.resolve().relative_to(_frontend_dir.resolve())`.

---

## 4. CORS Configuration

### FINDING-10: CORS configurado apropiadamente para uso local

- **Severidad:** INFO
- **Archivo:** `app/main.py` — middleware CORS
- **Líneas:** ~80-92
- **Descripción:** La configuración CORS es razonable para una aplicación local:
  - Origins restringidos a `localhost:3000`, `127.0.0.1:3000`, `localhost:5173`, `127.0.0.1:5173`
  - No usa `allow_origins=["*"]`
  - `allow_credentials=True` es necesario para el desarrollo local
  - `allow_methods=["*"]` y `allow_headers=["*"]` son permisivos pero aceptables para una app local
- **Nota:** En producción (frontend servido desde el mismo origen), CORS no aplica. La configuración actual solo es relevante durante desarrollo con Vite dev server.
- **Estado:** ✅ Aceptable para el caso de uso.

---

## 5. Denial of Service

### FINDING-11: Sin límite de tamaño de archivo para procesamiento

- **Severidad:** MEDIUM
- **Archivo:** `app/pdf/processor.py` y `app/api/routes.py`
- **Descripción:** No existe validación del tamaño de los archivos antes de procesarlos. Un archivo PDF de varios GB podría:
  - Consumir toda la memoria RAM al cargarse con PyMuPDF.
  - Bloquear el procesamiento NER con spaCy (que carga todo el texto en memoria).
  - Llenar el disco con archivos de salida.
- **Impacto:** Agotamiento de recursos del sistema (RAM, CPU, disco).
- **Fix recomendado:**
  - Implementar un límite configurable de tamaño de archivo (ej: 100MB).
  - Validar el tamaño antes de iniciar el procesamiento.
  - Agregar un timeout por archivo.

### FINDING-12: Sin límite de archivos concurrentes

- **Severidad:** LOW
- **Archivo:** `app/api/routes.py` — endpoint `POST /api/process`
- **Descripción:** Aunque existe un mutex básico (`_processing_state["active"]`) que previene procesamiento concurrente, no hay límite en la cantidad de archivos que se pueden procesar en un solo batch. Una carpeta con miles de archivos podría mantener el servidor ocupado indefinidamente.
- **Fix recomendado:**
  - Implementar un límite máximo de archivos por batch (ej: 100).
  - Agregar un timeout global para el procesamiento completo.
  - Considerar un mecanismo de cancelación.

### FINDING-13: Cola SSE sin límite de tamaño

- **Severidad:** LOW
- **Archivo:** `app/api/routes.py` — variable `_sse_events`
- **Descripción:** La cola `asyncio.Queue()` no tiene `maxsize`, lo que significa que si el cliente SSE no consume eventos, la cola crecerá indefinidamente en memoria.
- **Fix recomendado:**
  - Usar `asyncio.Queue(maxsize=1000)` para limitar el crecimiento.
  - Implementar descarte de eventos antiguos si la cola está llena.

---

## 6. Data Exposure

### FINDING-14: Log de auditoría expone nombres de archivos sensibles

- **Severidad:** MEDIUM
- **Archivo:** `app/log/service.py` y `log/audit.jsonl`
- **Descripción:** El log de auditoría registra los nombres completos de los archivos procesados. En el archivo `audit.jsonl` actual se observan nombres como:
  - `"cv-jperez-2026-infra-en.pdf"` — nombre de persona
  - `"Juan Pérez - Annual Review Q1 2026.pdf"` — nombre de persona + tipo de documento
  - `"Invoice_2353055989.pdf"` — número de factura
  
  Estos nombres de archivo pueden contener PII o información confidencial.
- **Impacto:** El log de auditoría, accesible vía API (`GET /api/logs`), expone información sobre qué documentos fueron procesados y por quién.
- **Fix recomendado:**
  - Considerar hashear o truncar los nombres de archivo en los logs.
  - Restringir el acceso al endpoint de logs.
  - Agregar una opción para anonimizar nombres de archivo en el log.

### FINDING-15: Respuestas de error exponen rutas internas del sistema

- **Severidad:** LOW
- **Archivo:** `app/api/file_service.py` y `app/exceptions.py`
- **Descripción:** Los mensajes de error de `PathValidationError` incluyen la ruta completa proporcionada por el usuario (ej: `"La ruta no existe: /ruta/completa"`). Esto es aceptable para una app local pero podría exponer información del sistema si la app se expone a red.
- **Estado:** Aceptable para uso local, pero considerar sanitizar en caso de exposición a red.

### FINDING-16: El endpoint output/files expone rutas absolutas

- **Severidad:** INFO
- **Archivo:** `app/api/routes.py` — endpoint `GET /api/output/files`
- **Descripción:** La respuesta incluye el campo `path` con la ruta absoluta completa de cada archivo ofuscado (ej: `/Users/usuario/Documents/.../ofuscados/archivo.pdf`). Esto expone la estructura del sistema de archivos del usuario.
- **Fix recomendado:**
  - Retornar solo rutas relativas al directorio base del proyecto.
  - El frontend no necesita la ruta absoluta ya que usa los endpoints de la API para acceder a los archivos.

---

## 7. Dependency Security

### FINDING-17: Dependencias Python sin versiones fijas (pinning)

- **Severidad:** INFO
- **Archivo:** `requirements.txt`
- **Descripción:** La mayoría de dependencias usan `>=` en lugar de versiones exactas pinneadas:
  ```
  fastapi>=0.115.0
  uvicorn>=0.34.0
  PyMuPDF>=1.25.0
  spacy>=3.7.0,<4.0.0
  pydantic>=2.10.0
  python-multipart>=0.0.20
  httpx>=0.28.0
  fpdf2>=2.8.0
  fpdf2==2.8.2  # duplicado con versión exacta
  python-docx>=1.1.0
  ```
  Además, `fpdf2` aparece duplicado (una vez con `>=` y otra con `==`).
- **Impacto:** Instalaciones futuras podrían obtener versiones con vulnerabilidades conocidas. La falta de pinning dificulta la reproducibilidad.
- **Fix recomendado:**
  - Usar `pip freeze > requirements.txt` para pinnear versiones exactas.
  - Eliminar la entrada duplicada de `fpdf2`.
  - Implementar escaneo periódico con `pip-audit`.
  - Considerar usar `pip-compile` (pip-tools) para gestión de dependencias.

### FINDING-18: Dependencias frontend con rangos amplios

- **Severidad:** INFO
- **Archivo:** `frontend/package.json`
- **Descripción:** Las dependencias usan rangos con `^` (ej: `"react": "^18.2.0"`), lo cual es estándar en el ecosistema Node.js. El `package-lock.json` existe y pinnea las versiones exactas.
- **Estado:** ✅ Aceptable. El lock file proporciona reproducibilidad.
- **Recomendación:** Ejecutar `npm audit` periódicamente.

---

## 8. Authentication / Authorization

### FINDING-19: Sin autenticación ni autorización

- **Severidad:** HIGH (condicional)
- **Archivo:** Toda la aplicación
- **Descripción:** La aplicación no implementa ningún mecanismo de autenticación o autorización. Cualquier persona con acceso a la red donde se ejecuta el servidor puede:
  - Navegar el sistema de archivos completo (`/api/folders/browse`)
  - Procesar cualquier documento del sistema
  - Ver y borrar archivos ofuscados
  - Leer el log de auditoría completo
  - Modificar la configuración
- **Contexto:** Para una aplicación estrictamente local (localhost), la falta de auth es aceptable. Sin embargo, el servidor se configura con `--host 0.0.0.0` (ver FINDING-20), lo que lo expone a toda la red local.
- **Impacto:** Si el servidor es accesible desde la red, cualquier dispositivo en la misma red puede acceder a todas las funcionalidades sin restricción.
- **Fix recomendado:**
  - **Opción A (mínima):** Cambiar el binding a `127.0.0.1` para que solo sea accesible desde localhost.
  - **Opción B (robusta):** Implementar autenticación básica (token o password) si se necesita acceso desde red.
  - **Opción C:** Agregar un middleware que valide que las requests vienen de `127.0.0.1` o `::1`.

---

## 9. Server Configuration

### FINDING-20: Servidor bindeado a 0.0.0.0 (todas las interfaces)

- **Severidad:** HIGH
- **Archivo:** `run.sh` — línea `HOST=${HOST:-0.0.0.0}`
- **Descripción:** El script `run.sh` configura uvicorn para escuchar en `0.0.0.0`, lo que expone el servidor a TODAS las interfaces de red del sistema (WiFi, Ethernet, VPN, etc.). Esto significa que cualquier dispositivo en la misma red puede acceder a la aplicación.
- **Impacto:** Combinado con la falta de autenticación (FINDING-19) y la capacidad de navegar el sistema de archivos (FINDING-01), esto permite a cualquier dispositivo en la red local:
  - Explorar el sistema de archivos del host
  - Leer documentos PDF/MD/DOCX de cualquier ubicación
  - Borrar archivos ofuscados
- **Fix recomendado:**
  - Cambiar el default a `HOST=${HOST:-127.0.0.1}` para que solo sea accesible desde localhost.
  - Si se necesita acceso desde red, documentar el riesgo y requerir autenticación.
  - Agregar un warning visible al usuario si se usa `0.0.0.0`.

### FINDING-21: Uvicorn sin configuración de producción

- **Severidad:** INFO
- **Archivo:** `run.sh`
- **Descripción:** Uvicorn se ejecuta sin flags de producción:
  - No se especifica `--workers` (single worker por defecto)
  - No se usa `--no-access-log` para reducir logging
  - No se configura `--limit-concurrency` ni `--limit-max-requests`
  - No se usa HTTPS/TLS
- **Contexto:** Para una aplicación local de escritorio, esta configuración es aceptable. No se espera tráfico concurrente significativo.
- **Estado:** Aceptable para el caso de uso local.

---

## 10. Frontend Security

### FINDING-22: Sin uso de dangerouslySetInnerHTML ni innerHTML

- **Severidad:** INFO (positivo)
- **Archivo:** Todos los componentes frontend
- **Descripción:** El frontend usa exclusivamente componentes de Cloudscape Design System y React JSX estándar. No se encontraron usos de:
  - `dangerouslySetInnerHTML`
  - `innerHTML` directo
  - `eval()` o `Function()`
  - Inyección de HTML sin escapar
- **Estado:** ✅ El frontend está bien protegido contra XSS.

### FINDING-23: URLs construidas con interpolación de strings

- **Severidad:** LOW
- **Archivo:** `frontend/src/pages/OutputPage.tsx`
- **Líneas:** ~130, ~145
- **Descripción:** Las URLs para ver archivos se construyen con template literals:
  ```typescript
  const url = `/api/output/view/${item.folder}/${item.name}`;
  window.open(url, '_blank');
  ```
  Si `item.name` contuviera caracteres especiales de URL (ej: `../`, `%2e%2e`), podría manipularse la ruta. Sin embargo, el backend valida path traversal en el endpoint receptor, mitigando el riesgo.
- **Fix recomendado:**
  - Usar `encodeURIComponent(item.name)` para sanitizar el nombre del archivo en la URL.

---

## Resumen de Hallazgos por Prioridad

### 🔴 CRITICAL (Acción inmediata requerida)

| ID | Hallazgo | Archivo |
|----|----------|---------|
| FINDING-08 | Procesamiento de archivos de cualquier ubicación | `app/api/routes.py` |

### 🟠 HIGH (Resolver antes de exponer a red)

| ID | Hallazgo | Archivo |
|----|----------|---------|
| FINDING-01 | Navegación de directorios sin restricciones | `app/api/routes.py` |
| FINDING-02 | Validación de carpetas sin restricción de directorio | `app/api/file_service.py` |
| FINDING-19 | Sin autenticación + binding 0.0.0.0 | Toda la app |
| FINDING-20 | Servidor bindeado a 0.0.0.0 | `run.sh` |

### 🟡 MEDIUM (Resolver en próxima iteración)

| ID | Hallazgo | Archivo |
|----|----------|---------|
| FINDING-05 | Falta sanitización de caracteres nulos en path | `app/api/routes.py` |
| FINDING-06 | Custom regex sin validación (ReDoS) | `frontend/src/pages/ConfigPage.tsx` |
| FINDING-11 | Sin límite de tamaño de archivo | `app/pdf/processor.py` |
| FINDING-14 | Log expone nombres de archivos sensibles | `app/log/service.py` |
| FINDING-03 | output/view protegido correctamente | `app/api/routes.py` |

### 🟢 LOW (Mejoras recomendadas)

| ID | Hallazgo | Archivo |
|----|----------|---------|
| FINDING-04 | delete sin validación de folder | `app/api/routes.py` |
| FINDING-07 | Config acepta JSON arbitrario | `app/api/routes.py` |
| FINDING-09 | serve_spa sin validación explícita | `app/main.py` |
| FINDING-12 | Sin límite de archivos por batch | `app/api/routes.py` |
| FINDING-13 | Cola SSE sin maxsize | `app/api/routes.py` |
| FINDING-23 | URLs sin encodeURIComponent | `frontend/src/pages/OutputPage.tsx` |

### ℹ️ INFO (Observaciones)

| ID | Hallazgo | Estado |
|----|----------|--------|
| FINDING-10 | CORS configurado correctamente | ✅ OK |
| FINDING-15 | Errores exponen rutas (aceptable local) | ✅ OK para local |
| FINDING-16 | Rutas absolutas en respuestas | Mejorable |
| FINDING-17 | Dependencias sin pinning | Mejorable |
| FINDING-18 | Frontend deps con lock file | ✅ OK |
| FINDING-21 | Uvicorn sin config producción | ✅ OK para local |
| FINDING-22 | Sin XSS en frontend | ✅ OK |

---

## Recomendaciones Prioritarias

### 1. Cambiar binding por defecto a 127.0.0.1 (Quick Win)
```bash
# run.sh
HOST=${HOST:-127.0.0.1}  # En lugar de 0.0.0.0
```
Esto elimina inmediatamente la exposición a la red local.

### 2. Implementar restricción de directorio base
```python
# app/api/file_service.py
ALLOWED_BASE_DIRS = [Path.home()]  # O configurar vía variable de entorno

def validate_path(path_str: str) -> Path:
    path = Path(path_str).resolve()
    # Verificar que está dentro de un directorio permitido
    if not any(path.is_relative_to(base) for base in ALLOWED_BASE_DIRS):
        raise PathValidationError(
            code="ACCESS_DENIED",
            message="La ruta está fuera de los directorios permitidos.",
            recoverable=True,
        )
    # ... resto de validaciones
```

### 3. Validar folder en endpoint delete
```python
# app/api/routes.py — POST /api/output/delete
if request.folder not in ("ofuscados", "ofuscados_md"):
    raise HTTPException(status_code=422, detail={...})
```

### 4. Agregar límite de tamaño de archivo
```python
MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024  # 100 MB

# Antes de procesar cada archivo:
if file_info.size_bytes > MAX_FILE_SIZE_BYTES:
    # Emitir error y saltar archivo
```

### 5. Sanitizar nombres de archivo en logs
Considerar registrar solo un hash o versión truncada del nombre de archivo para proteger la privacidad.

---

## Conclusión

DataMask es una aplicación local bien estructurada con buenas prácticas en varias áreas (protección de path traversal en endpoints de output, uso de Pydantic para validación, frontend sin XSS). Los principales riesgos provienen de:

1. **La combinación de binding a `0.0.0.0` + sin autenticación + acceso irrestricto al filesystem** — esto convierte una herramienta local segura en un potencial vector de exfiltración de datos si hay otros dispositivos en la red.

2. **La falta de restricción de directorios** — la app puede leer/procesar archivos de cualquier ubicación del sistema.

Para uso estrictamente local (un solo usuario en su máquina), el riesgo real es bajo. Sin embargo, el cambio de binding a `127.0.0.1` es un quick win que elimina la mayoría de los vectores de ataque sin impacto funcional.
