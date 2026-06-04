# Requisitos Técnicos — DataMask v3.2.2

## Requisitos de Hardware

| Componente | Mínimo | Recomendado |
|------------|--------|-------------|
| RAM | 8 GB | 16 GB |
| Espacio en disco | 10 GB libres | 15 GB libres |
| CPU | 4 cores | 8 cores |
| GPU | No requerida | Opcional (acelera Ollama) |

> **Nota:** El modelo Llama 3.1 8B requiere ~4.7GB de RAM para inferencia. Con el sistema operativo y la aplicación, se necesitan mínimo 8GB totales.

---

## Requisitos de Software

### Sistema Operativo

| OS | Versión mínima |
|----|---------------|
| macOS | 12 (Monterey) o superior |
| Windows | 10 (64-bit) o superior |

### Dependencias de Software

| Software | Versión | Propósito | Tamaño |
|----------|---------|-----------|--------|
| Python | >= 3.9 | Backend de la aplicación | ~100MB |
| Node.js | >= 18 | Frontend React | ~100MB |
| Ollama | Última versión | Motor de IA para detección de nombres y direcciones | ~500MB |
| Modelo Llama 3.1 8B | Q4_0 (cuantizado) | Modelo de lenguaje para NER | ~4.7GB |

### Dependencias Python (instaladas automáticamente)

| Paquete | Versión | Propósito |
|---------|---------|-----------|
| FastAPI | >= 0.115.0 | Framework web backend |
| Uvicorn | >= 0.34.0 | Servidor ASGI |
| PyMuPDF | >= 1.25.0 | Procesamiento de PDFs |
| python-docx | >= 1.1.0 | Procesamiento de Word |
| Pydantic | >= 2.10.0 | Validación de datos |
| httpx | >= 0.28.0 | Cliente HTTP (comunicación con Ollama) |
| fpdf2 | >= 2.8.0 | Generación de PDFs de test |

### Dependencias Frontend (instaladas automáticamente)

| Paquete | Propósito |
|---------|-----------|
| React 18 | Framework UI |
| Cloudscape Design System | Componentes de interfaz |
| TypeScript 5 | Tipado estático |
| Vite 5 | Bundler |

---

## Arquitectura de IA

### Motor de Detección Híbrido

DataMask usa un enfoque híbrido para la detección de datos sensibles:

```
┌─────────────────────────────────────────────────────┐
│              MOTOR DE DETECCIÓN HÍBRIDO              │
├─────────────────────────┬───────────────────────────┤
│     Ollama (LLM)        │     Regex (Patrones)      │
│                         │                           │
│  • Nombres y apellidos  │  • DNI (XX.XXX.XXX)      │
│  • Direcciones postales │  • CUIT/CUIL             │
│  • Contexto semántico   │  • Teléfonos (+XX...)    │
│                         │  • Emails                │
│  Modelo: Llama 3.1 8B   │  • Tarjetas de crédito  │
│  Precisión: ~95%        │  • CBU (22 dígitos)      │
│  Velocidad: 2-5s/página │  • Pasaportes            │
│                         │                           │
│                         │  Precisión: ~100%         │
│                         │  Velocidad: <0.01s/página │
└─────────────────────────┴───────────────────────────┘
```

### ¿Por qué Ollama + Regex?

| Aspecto | Solo Regex | Solo LLM | Híbrido (elegido) |
|---------|-----------|----------|-------------------|
| Nombres en mayúsculas | ❌ No detecta | ✅ Detecta | ✅ Detecta |
| Nombres poco comunes | ❌ No detecta | ✅ Detecta | ✅ Detecta |
| Direcciones complejas | ❌ Parcial | ✅ Detecta | ✅ Detecta |
| DNI/CUIT/Email | ✅ 100% preciso | ⚠️ ~90% | ✅ 100% (regex) |
| Velocidad | ⚡ Instantáneo | 🐢 2-5s/pág | ⚡ Rápido para formatos + 2-5s para nombres |
| RAM requerida | 1GB | 8GB | 8GB |

### Modelo: configurable (por defecto Llama 3.1 8B)

DataMask permite elegir el modelo de Ollama desde la página de Configuración y descargar nuevos modelos sin salir de la app. El modelo por defecto es `llama3.1:8b`.

- **Por defecto:** Llama 3.1 8B (Meta AI), cuantización Q4_0 (~4.7GB), multilingüe
- **Alternativas recomendadas:** `qwen2.5:7b` (~4.7GB), `qwen2.5:3b` (~1.9GB), `llama3.2:3b`
- **Licencia (Llama):** Llama 3.1 Community License (uso comercial permitido)
- **Ejecución:** 100% local vía Ollama, sin conexión a internet

> ⚠️ **Precaución con modelos grandes:** modelos de 14B+ parámetros (ej: `qwen3.6` de ~23GB) pueden agotar la RAM y congelar la máquina. Se recomienda usar modelos de ≤8B parámetros salvo que la máquina tenga RAM suficiente (32GB+).

### Comunicación con Ollama

```
DataMask Backend ──HTTP──▶ Ollama API (localhost:11434)
                          │
                          ▼
                    Llama 3.1 8B
                    (inferencia local)
```

- Protocolo: HTTP REST
- Endpoint: `http://localhost:11434/api/generate`
- Timeout: 60 segundos por request (configurable en `config/ollama.json`)
- Sin conexión a internet requerida

---

## Puertos de Red

| Servicio | Puerto | Acceso |
|----------|--------|--------|
| DataMask (web UI) | 3000 | Solo localhost (127.0.0.1) |
| Ollama API | 11434 | Solo localhost (127.0.0.1) |

Ambos servicios solo escuchan en localhost. No son accesibles desde la red.

---

## Espacio en Disco Detallado

| Componente | Tamaño |
|------------|--------|
| Ollama (binario) | ~500MB |
| Modelo Llama 3.1 8B (Q4_0) | ~4.7GB |
| Dependencias Python (venv) | ~500MB |
| Dependencias Frontend (node_modules) | ~300MB |
| Frontend build | ~2MB |
| Código fuente | ~1MB |
| **Total instalación** | **~6GB** |
| Espacio para archivos procesados | Variable |

---

## Proceso de Instalación

### macOS

```bash
# 1. Clonar repositorio
git clone https://github.com/Eduvilascoder/DataMask.git
cd DataMask

# 2. Ejecutar instalador (instala todo incluyendo Ollama)
chmod +x setup.sh run.sh stop.sh
./setup.sh

# 3. Iniciar la aplicación
./run.sh
```

### Windows

```cmd
# 1. Clonar repositorio
git clone https://github.com/Eduvilascoder/DataMask.git
cd DataMask

# 2. Ejecutar instalador
setup.bat

# 3. Iniciar la aplicación
run.bat
```

### Qué instala el setup automáticamente

1. Verifica prerequisitos (Python, Node.js, espacio en disco)
2. Instala Ollama (si no está instalado)
3. Descarga el modelo Llama 3.1 8B (~4.7GB, primera vez solamente)
4. Crea entorno virtual Python e instala dependencias
5. Instala dependencias del frontend y genera build
6. Crea estructura de carpetas del proyecto

> ⏱️ Primera instalación: ~10-15 minutos (depende de la velocidad de internet para descargar el modelo)

---

## Verificación Post-Instalación

```bash
# Verificar que Ollama está corriendo
curl http://localhost:11434/api/tags

# Verificar que el modelo está disponible
ollama list | grep llama3.1

# Verificar que DataMask responde
curl http://localhost:3000/api/health
```

---

## Troubleshooting

### Ollama no inicia

```bash
# macOS: verificar que el servicio está corriendo
ollama serve &

# Windows: iniciar desde el menú de inicio o
ollama serve
```

### Modelo no descargado

```bash
ollama pull llama3.1:8b
```

### Error "out of memory"

El modelo requiere ~5GB de RAM libre. Cierre aplicaciones que consuman mucha memoria antes de procesar documentos.

### Procesamiento muy lento

- Verificar que no hay otros procesos usando la GPU/CPU intensivamente
- Considerar procesar menos archivos por batch
- En máquinas con GPU NVIDIA, Ollama usa CUDA automáticamente (más rápido)
