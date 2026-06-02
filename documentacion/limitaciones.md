# Limitaciones Conocidas — DataMask v3.0

## Documentos embebidos

| Tipo de embebido | Estado | Detalle |
|-----------------|--------|---------|
| PDF dentro de PDF | ✅ Soportado | Se extraen, ofuscan y reincrustan automáticamente |
| Imágenes con texto | ❌ No soportado | No se aplica OCR. El texto dentro de imágenes no se detecta ni ofusca |
| Excel embebido (.xlsx) | ❌ No soportado | Los archivos Excel adjuntos dentro de un PDF se ignoran |
| Word embebido (.docx) | ❌ No soportado | Los archivos Word adjuntos dentro de un PDF se ignoran |
| Formularios PDF (campos) | ⚠️ Parcial | Se ofusca el texto visible pero no los campos de formulario editables |

---

## Tamaño de documentos

| Limitación | Valor | Impacto |
|-----------|-------|---------|
| Texto enviado a Ollama | Máximo 3000 caracteres por página | Páginas con más texto se truncan. Datos sensibles al final de una página muy larga podrían no detectarse |
| Tamaño de archivo | Sin límite técnico | Archivos > 50MB pueden tardar varios minutos y consumir mucha RAM |
| RAM para procesamiento | Depende del tamaño del PDF | Un PDF de 100+ páginas puede requerir 2-3GB de RAM adicional |
| Timeout de Ollama | 30 segundos por página | Si Ollama tarda más de 30 segundos en responder por una página, se omite esa página |

---

## Detección de datos sensibles

| Limitación | Detalle |
|-----------|---------|
| Precisión del modelo | ~85-95%. No garantiza detección del 100% de datos sensibles |
| Nombres poco comunes | spaCy puede fallar con nombres que no están en su vocabulario. Ollama es significativamente mejor |
| Texto en imágenes | No se detecta. Solo se procesa texto extraíble del PDF |
| Texto escaneado (OCR) | No se soporta. PDFs que son imágenes escaneadas no se pueden procesar |
| Idiomas | Optimizado para español. Funciona parcialmente en inglés y portugués. Otros idiomas no están garantizados |
| Contexto cross-página | Cada página se procesa independientemente. Un nombre que empieza en una página y termina en otra no se detecta como unidad |
| Falsos positivos | Números que coinciden con patrones (ej: un código de 8 dígitos puede detectarse como DNI) |
| Tablas complejas | El texto de tablas puede extraerse desordenado, dificultando la detección de entidades |

---

## Formato de salida (PDF)

| Limitación | Detalle |
|-----------|---------|
| Fuente de la etiqueta | Las etiquetas [TIPO] usan Helvetica, Times o Courier (fuentes built-in de PDF). Si el original usa una fuente custom, la etiqueta puede verse ligeramente diferente |
| Tamaño de etiqueta | Se usa el mismo tamaño de fuente del texto original, pero la etiqueta puede ser más larga o corta que el texto reemplazado |
| Layout del PDF | La redacción puede alterar ligeramente el layout si la etiqueta es más larga que el texto original |
| Metadatos del PDF | Los metadatos del documento (autor, título, etc.) no se ofuscan |
| Anotaciones | Las anotaciones y comentarios del PDF no se procesan |
| Capas (layers) | Solo se procesa la capa de texto principal. Texto en otras capas puede no detectarse |

---

## Formato de salida (Word .docx)

| Limitación | Detalle |
|-----------|---------|
| Formato de runs | Al ofuscar, se reemplaza el texto del primer run del párrafo. El formato (negrita, cursiva, color) del texto original puede no preservarse completamente |
| Headers/Footers | Los encabezados y pies de página no se procesan |
| Tablas en Word | Las tablas dentro del documento Word no se procesan |
| Imágenes en Word | El texto dentro de imágenes o cuadros de texto no se procesa |
| Comentarios | Los comentarios del documento no se ofuscan |

---

## Infraestructura y sistema

| Limitación | Detalle |
|-----------|---------|
| Procesamiento concurrente | Solo se procesa un batch a la vez. No se pueden iniciar dos procesamientos simultáneos |
| Carpetas recursivas | Solo se procesan archivos en el nivel superior de la carpeta seleccionada. No se exploran subcarpetas |
| Autenticación | No hay autenticación de usuario. Cualquier persona con acceso al navegador puede usar la app |
| Acceso a la red | Solo accesible desde localhost (127.0.0.1). No es accesible desde otros dispositivos |
| Sistema operativo | Solo macOS 12+ y Windows 10+ (64-bit). No soporta Linux ni ARM nativo (excepto macOS Apple Silicon) |
| Ollama en Windows | Ollama puede no agregar automáticamente al PATH. Usar `fixpath.bat` si no se detecta |

---

## Ollama (Motor de IA)

| Limitación | Detalle |
|-----------|---------|
| RAM requerida | Mínimo 8GB (5GB para el modelo + 3GB para OS y app) |
| Primera inferencia | La primera llamada a Ollama después de iniciar es más lenta (~5-10 segundos) porque carga el modelo en memoria |
| Consistencia | Ollama no es 100% determinístico (temperature=0.1). Puede haber variaciones mínimas entre ejecuciones |
| Timeout | Si Ollama tarda > 30 segundos por página, se omite esa página y se usa spaCy como fallback |
| Modelo offline | El modelo debe descargarse durante la instalación (requiere internet). Después funciona offline |

---

## Workarounds conocidos

| Problema | Solución |
|---------|----------|
| Texto en imágenes no detectado | Convertir el PDF a texto con un software OCR (Adobe, ABBYY) antes de procesarlo con DataMask |
| Archivo muy grande es lento | Dividir el PDF en partes más pequeñas antes de procesarlo |
| Nombre no detectado | Agregar una regla específica en el prompt de Ollama, o agregar un tipo custom con patrón regex |
| Falso positivo frecuente | Desactivar el tipo que causa el falso positivo en Configuración |
| Ollama no detectado | Ejecutar `fixpath.bat` (Windows) o verificar que `ollama serve` esté corriendo |
