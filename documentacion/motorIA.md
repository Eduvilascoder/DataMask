# Motores de IA — Ollama vs spaCy

## Resumen

DataMask ofrece dos motores de inteligencia artificial para la detección de datos sensibles. Ambos se ejecutan 100% localmente sin enviar datos a internet.

| | Ollama (Llama 3.1 8B) | spaCy (es_core_news_lg) |
|---|---|---|
| **Tipo** | Large Language Model (LLM) | Pipeline NLP especializado |
| **Precisión nombres** | ~95% | ~70-80% |
| **Velocidad** | 2-5 seg/página | 0.1 seg/página |
| **RAM requerida** | ~5 GB | ~1 GB |
| **Tamaño modelo** | 4.7 GB | 560 MB |
| **Nombres en mayúsculas** | Excelente | Limitado |
| **Nombres poco comunes** | Excelente | Falla frecuentemente |
| **Direcciones complejas** | Excelente | Parcial |

---

## ¿Qué es Ollama?

**Ollama** es una plataforma que permite ejecutar modelos de lenguaje grandes (LLMs) de forma local en tu máquina. Es similar a ChatGPT pero corre completamente offline.

### Modelo usado: Llama 3.1 8B

- **Desarrollador:** Meta AI (Facebook)
- **Parámetros:** 8 mil millones
- **Tipo:** Modelo de lenguaje generativo multilingüe
- **Licencia:** Llama 3.1 Community License (uso comercial permitido)

### Cómo funciona en DataMask

DataMask envía el texto del documento a Ollama con un prompt especializado que le pide identificar nombres de personas y direcciones. El modelo "entiende" el contexto semántico del texto — sabe que "JUAN PÉREZ GONZÁLEZ" al inicio de un CV es un nombre completo, sin importar si está en mayúsculas o si los nombres no son comunes.

```
Texto del documento → Ollama (localhost:11434) → Lista de nombres y direcciones detectados
```

### Ventajas de Ollama

- **Comprensión semántica:** Entiende el contexto. Sabe que "Santiago, Chile" después de un nombre es una ubicación, no parte del nombre.
- **Nombres en cualquier formato:** Detecta nombres en MAYÚSCULAS, minúsculas, con acentos, nombres poco comunes, nombres extranjeros.
- **Direcciones complejas:** Reconoce "Av. Corrientes 1234, Piso 5, CABA, Buenos Aires" como una dirección completa.
- **Sin vocabulario fijo:** No depende de un diccionario de nombres — puede detectar cualquier nombre que un humano reconocería.

### Desventajas de Ollama

- **Más lento:** 2-5 segundos por página (vs 0.1 segundos con spaCy)
- **Más RAM:** Requiere ~5 GB de RAM libre para el modelo
- **Instalación más pesada:** El modelo ocupa 4.7 GB en disco
- **Requiere servicio activo:** Ollama debe estar corriendo como servicio en background

---

## ¿Qué es spaCy?

**spaCy** es una librería de procesamiento de lenguaje natural (NLP) especializada en tareas como reconocimiento de entidades nombradas (NER), análisis sintáctico y tokenización.

### Modelo usado: es_core_news_lg

- **Desarrollador:** Explosion AI
- **Tipo:** Pipeline CNN (Convolutional Neural Network)
- **Entrenamiento:** Corpus AnCora + WikiNER (textos en español)
- **Licencia:** MIT (código abierto)

### Cómo funciona en DataMask

spaCy analiza el texto token por token y clasifica cada secuencia de tokens según patrones aprendidos durante el entrenamiento. Reconoce entidades como PER (personas) y LOC (ubicaciones) basándose en el contexto gramatical y estadístico.

```
Texto del documento → spaCy (en memoria) → Entidades PER/LOC detectadas
```

### Ventajas de spaCy

- **Muy rápido:** 0.1 segundos por página (20-50x más rápido que Ollama)
- **Poco RAM:** Solo ~1 GB de memoria
- **Sin servicio externo:** Se ejecuta directamente en el proceso de Python
- **Modelo más liviano:** 560 MB vs 4.7 GB

### Desventajas de spaCy

- **Vocabulario limitado:** Solo reconoce nombres que son similares a los de su corpus de entrenamiento
- **Falla con mayúsculas:** "JUAN PÉREZ" en mayúsculas no se reconoce como nombre
- **Nombres poco comunes:** Nombres que no son típicos del español (ej: "Bitrera") pueden no detectarse
- **Direcciones parciales:** Solo detecta ciudades/países individuales, no direcciones completas

---

## ¿Cuándo usar cada uno?

### Usar Ollama cuando:

- Procesás documentos con nombres poco comunes o extranjeros
- Los documentos tienen texto en MAYÚSCULAS (CVs, formularios oficiales)
- Necesitás máxima precisión en la detección
- Tenés una máquina con al menos 8 GB de RAM
- No te importa que tarde unos segundos más por página

### Usar spaCy cuando:

- Necesitás procesar muchos documentos rápidamente
- Los nombres son comunes en español (Juan, María, García, López)
- La máquina tiene poca RAM (< 8 GB)
- No podés instalar Ollama (restricciones de sistema)
- Priorizás velocidad sobre precisión

---

## Enfoque híbrido

DataMask siempre complementa ambos motores con **patrones regex** para formatos estructurados. Independientemente de si usás Ollama o spaCy, los siguientes datos se detectan con regex (100% de precisión):

- DNI (XX.XXX.XXX)
- CUIT/CUIL (XX-XXXXXXXX-X)
- Teléfonos (+54..., +56..., etc.)
- Emails (usuario@dominio.com)
- Tarjetas de crédito (XXXX-XXXX-XXXX-XXXX)
- CBU (22 dígitos)
- Pasaportes (AAX######)

Además, DataMask incluye una **heurística de nombres en mayúsculas** que funciona con ambos motores: detecta líneas con 2-5 palabras en mayúsculas que parecen nombres propios (excluyendo títulos de cargo como "SOLUTIONS ARCHITECT").

---

## Configuración

Podés cambiar el motor y el modelo de Ollama en cualquier momento desde la sección
**Configuración** de la aplicación. Desde ahí también podés descargar nuevos modelos
de Ollama y ajustar la temperatura. El cambio aplica al próximo procesamiento — los
archivos ya procesados no se re-procesan automáticamente.

> El motor por defecto de Ollama es `llama3.1:8b`. La tabla comparativa de arriba
> usa ese modelo como referencia, pero los números (velocidad, RAM) varían según el
> modelo que elijas. Modelos más chicos (ej: `qwen2.5:3b`) son más rápidos y usan
> menos RAM a costa de algo de precisión.

El indicador de estado en la página de Procesamiento muestra qué motor y modelo está activo:

- 🟢 **Ollama activo (modelo configurado, ej: llama3.1:8b / qwen2.5:7b)** — máxima precisión
- 🔵 **Ollama deshabilitado — usando spaCy** — elegido por el usuario
- 🟡 **spaCy activo (Ollama no disponible)** — fallback automático
- 🔴 **Sin motor NER** — ningún motor disponible

> El modelo de Ollama se elige desde la página de Configuración. Desde ahí también
> se puede descargar un modelo nuevo y ajustar la temperatura. El modelo usado en
> cada procesamiento queda registrado en el log de auditoría.
