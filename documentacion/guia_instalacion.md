# Guía de Instalación

## Prerequisitos del Sistema

Antes de instalar la aplicación, asegúrese de contar con los siguientes requisitos:

| Requisito | Versión mínima | Notas |
|-----------|---------------|-------|
| Python | >= 3.9 | Incluir pip (se instala con Python) |
| Node.js | >= 18 | Incluye npm automáticamente |
| Espacio en disco | 2 GB libres | El modelo de IA ocupa ~560MB |
| Sistema operativo | macOS 12+ o Windows 10+ | |
| Conexión a internet | Solo durante la instalación | Para descargar dependencias y el modelo de IA |

### Verificar prerequisitos manualmente

**Python:**
```bash
python3 --version   # macOS
python --version    # Windows
```

**Node.js:**
```bash
node --version
npm --version
```

---

## Instalación en macOS

### Paso 1: Descargar el proyecto

Clone o descargue el repositorio en su máquina local.

### Paso 2: Dar permisos de ejecución al instalador

Abra una terminal en el directorio del proyecto y ejecute:

```bash
chmod +x setup.sh
chmod +x run.sh
```

### Paso 3: Ejecutar el instalador

```bash
./setup.sh
```

### Qué hace el instalador (`setup.sh`)

El script realiza las siguientes acciones en orden:

1. **Verifica prerequisitos**: Python >= 3.9, Node.js >= 18, espacio en disco (2GB), permisos de escritura
2. **Crea la estructura de directorios**: `log/`, `ofuscados/`, `test/`, `documentacion/`, `models/`, `config/`
3. **Crea un entorno virtual de Python**: `venv/` (aísla las dependencias del proyecto)
4. **Instala dependencias de Python**: FastAPI, PyMuPDF, spaCy, Pydantic, etc.
5. **Descarga el modelo de IA**: `es_core_news_lg` de spaCy (~560MB) con verificación de integridad
6. **Instala dependencias del frontend**: paquetes npm (React, Cloudscape, etc.)
7. **Genera el build del frontend**: compila TypeScript y empaqueta con Vite

### Resultado esperado

Al finalizar exitosamente, verá:

```
============================================================
  ¡Instalación completada exitosamente!
============================================================

La aplicación está lista para ejecutarse.

  Para iniciar la aplicación:

    ./run.sh
```

---

## Instalación en Windows

### Paso 1: Descargar el proyecto

Clone o descargue el repositorio en su máquina local.

### Paso 2: Ejecutar el instalador

Abra una terminal (CMD o PowerShell) en el directorio del proyecto y ejecute:

```cmd
setup.bat
```

> **Nota**: Si usa PowerShell, ejecute `cmd /c setup.bat` o abra CMD directamente.

### Qué hace el instalador (`setup.bat`)

El script realiza las mismas acciones que la versión macOS:

1. **Verifica prerequisitos**: Python >= 3.9, Node.js >= 18, espacio en disco, permisos de escritura
2. **Crea la estructura de directorios**: `log\`, `ofuscados\`, `test\`, `documentacion\`, `models\`, `config\`
3. **Crea un entorno virtual de Python**: `venv\`
4. **Instala dependencias de Python** desde `requirements.txt`
5. **Descarga el modelo de IA**: `es_core_news_lg` con verificación de integridad
6. **Instala dependencias del frontend** y genera el build

### Resultado esperado

Al finalizar exitosamente, verá:

```
============================================================
  Instalacion completada exitosamente!
============================================================

La aplicacion esta lista para ejecutarse.

  Para iniciar la aplicacion:

    run.bat
```

> **Importante en Windows**: Asegúrese de que Python esté agregado al PATH del sistema. Durante la instalación de Python, marque la opción "Add Python to PATH".

---

## Verificar la Instalación Correcta

Después de ejecutar el instalador, verifique que todo funciona correctamente:

### 1. Verificar la estructura de carpetas

Confirme que existen las siguientes carpetas en el directorio del proyecto:

```
PDF-Datos-Sensibles/
├── venv/           ← Entorno virtual de Python
├── log/            ← Carpeta para registros de auditoría
├── ofuscados/      ← Carpeta para PDFs ofuscados
├── test/           ← Carpeta con PDFs de ejemplo
├── documentacion/  ← Documentación del proyecto
├── models/         ← Modelo de IA
├── config/         ← Configuración persistente
└── frontend/
    ├── node_modules/  ← Dependencias del frontend
    └── build/          ← Build compilado del frontend
```

### 2. Verificar el modelo de IA

Active el entorno virtual y verifique que el modelo carga correctamente:

**macOS:**
```bash
source venv/bin/activate
python -c "import spacy; nlp = spacy.load('es_core_news_lg'); print('Modelo OK:', nlp.meta['name'])"
```

**Windows:**
```cmd
venv\Scripts\activate.bat
python -c "import spacy; nlp = spacy.load('es_core_news_lg'); print('Modelo OK:', nlp.meta['name'])"
```

Resultado esperado: `Modelo OK: core_news_lg`

### 3. Verificar el servidor

Inicie la aplicación y confirme que el servidor responde:

**macOS:**
```bash
./run.sh
```

**Windows:**
```cmd
run.bat
```

Luego abra en su navegador: **http://localhost:3000**

Debería ver la interfaz de la aplicación con el panel de selección de carpeta.

### 4. Prueba funcional rápida

1. En la interfaz, ingrese la ruta de la carpeta `test/` del proyecto
2. Valide la carpeta — debería listar 3 archivos PDF de ejemplo
3. Ejecute el procesamiento
4. Verifique que se generaron archivos en la carpeta `ofuscados/`

---

## Resolución de Problemas Comunes

### La descarga del modelo de IA falla

**Síntoma**: El instalador muestra un error al descargar `es_core_news_lg`.

**Causas posibles**:
- Sin conexión a internet
- Espacio en disco insuficiente (el modelo requiere ~560MB)
- Interrupción de la descarga (timeout de red)

**Solución**:

1. Verifique su conexión a internet
2. Libere espacio en disco si es necesario
3. Reintente la descarga manualmente:

```bash
# macOS
source venv/bin/activate
python -m spacy download es_core_news_lg

# Windows
venv\Scripts\activate.bat
python -m spacy download es_core_news_lg
```

Si la descarga se interrumpe repetidamente, intente desde una red más estable o use una conexión por cable.

---

### El puerto 3000 está en uso

**Síntoma**: Al iniciar la aplicación, aparece un error indicando que el puerto está ocupado.

**Solución**:

Opción 1 — Usar un puerto alternativo:

```bash
# macOS
PORT=3001 ./run.sh

# Windows
set PORT=3001 && run.bat
```

Opción 2 — Identificar y detener el proceso que ocupa el puerto:

```bash
# macOS
lsof -i :3000
kill -9 <PID>

# Windows
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

---

### Error de permisos al crear carpetas o escribir archivos

**Síntoma**: El instalador o la aplicación muestra errores de permisos.

**Solución macOS**:

```bash
# Dar permisos al directorio del proyecto
chmod -R u+rwX /ruta/al/proyecto/PDF-Datos-Sensibles

# Dar permisos de ejecución a los scripts
chmod +x setup.sh run.sh
```

**Solución Windows**:

- Ejecute la terminal como **Administrador**
- O mueva el proyecto a una ubicación donde tenga permisos de escritura (ej: `C:\Users\<usuario>\Proyectos\`)

---

### `python` no se reconoce como comando (Windows)

**Síntoma**: Al ejecutar `setup.bat`, aparece "'python' no se reconoce como un comando interno o externo".

**Solución**:

1. Reinstale Python desde [python.org](https://www.python.org/downloads/)
2. Durante la instalación, **marque la casilla "Add Python to PATH"**
3. Reinicie la terminal después de la instalación
4. Verifique con: `python --version`

Si ya tiene Python instalado pero no está en el PATH:
1. Busque "Variables de entorno" en el menú de inicio
2. Edite la variable `Path` del usuario
3. Agregue la ruta de instalación de Python (ej: `C:\Users\<usuario>\AppData\Local\Programs\Python\Python312\`)
4. Agregue también la carpeta `Scripts\` (ej: `C:\Users\<usuario>\AppData\Local\Programs\Python\Python312\Scripts\`)

---

### `node` no se reconoce como comando

**Síntoma**: El instalador no encuentra Node.js.

**Solución**:

1. Descargue e instale Node.js desde [nodejs.org](https://nodejs.org/) (versión LTS recomendada)
2. Reinicie la terminal después de la instalación
3. Verifique con: `node --version`

---

### El modelo de IA parece corrupto

**Síntoma**: La aplicación inicia pero falla al procesar PDFs con errores relacionados al modelo spaCy.

**Solución**:

Desinstale y reinstale el modelo:

```bash
# Activar entorno virtual primero
source venv/bin/activate          # macOS
venv\Scripts\activate.bat         # Windows

# Reinstalar modelo
pip uninstall es_core_news_lg -y
python -m spacy download es_core_news_lg
```

---

### Error al instalar dependencias de Python (pip)

**Síntoma**: `pip install -r requirements.txt` falla con errores de compilación.

**Solución**:

- **macOS**: Instale las herramientas de desarrollo de Xcode:
  ```bash
  xcode-select --install
  ```

- **Windows**: Instale [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) si algún paquete requiere compilación nativa.

- Actualice pip antes de reintentar:
  ```bash
  pip install --upgrade pip
  pip install -r requirements.txt
  ```

---

### El frontend no se muestra (página en blanco)

**Síntoma**: El servidor inicia pero el navegador muestra una página en blanco.

**Solución**:

Regenere el build del frontend:

```bash
cd frontend
npm install
npm run build
cd ..
```

Luego reinicie la aplicación con `./run.sh` o `run.bat`.
