# Requirements Document

## Introduction

Aplicación web local para la ofuscación automática de datos sensibles en archivos PDF. La aplicación permite al usuario seleccionar una carpeta con archivos PDF, detectar datos personales sensibles (con foco en formatos argentinos) y reemplazarlos por etiquetas descriptivas entre corchetes (ej: `[EMAIL]`). La solución corre 100% localmente sin dependencias de servicios en la nube, utiliza el framework Cloudscape para la interfaz de usuario y toda la UI se presenta en español.

## Glossary

- **Sistema**: La aplicación web local de ofuscación de datos sensibles en PDFs
- **Usuario**: Persona que opera la aplicación a través de la interfaz web
- **Carpeta_Origen**: Directorio del sistema de archivos que contiene los PDFs a procesar
- **Dato_Sensible**: Información personal identificable que debe ser ofuscada (nombre, email, teléfono, etc.)
- **Tipo_Dato_Sensible**: Categoría configurada de dato sensible (ej: EMAIL, DNI, TELEFONO)
- **Etiqueta_Ofuscación**: Texto de reemplazo en formato `[TIPO]` que sustituye al dato sensible detectado
- **Motor_NER**: Modelo de reconocimiento de entidades nombradas que se ejecuta localmente para detectar datos sensibles
- **Registro_Log**: Entrada en el archivo de auditoría con información de cada archivo procesado
- **Instalador**: Script de configuración automática del entorno (setup.sh para Mac, setup.bat para Windows)
- **Configuración_Tipos**: Conjunto de tipos de datos sensibles activos para la detección
- **Carpeta_Ofuscados**: Subdirectorio `ofuscados/` dentro del directorio de la aplicación donde se almacenan los PDFs ofuscados generados
- **Carpeta_Log**: Subdirectorio `log/` dentro del directorio de la aplicación donde se almacenan los archivos de registro de auditoría
- **Carpeta_Test**: Subdirectorio `test/` dentro del directorio de la aplicación que contiene archivos PDF de ejemplo con datos sensibles ficticios para verificar el correcto funcionamiento de la ofuscación
- **Carpeta_Documentacion**: Subdirectorio `documentacion/` dentro del directorio de la aplicación que contiene la documentación completa del proyecto (arquitectura, guía de usuario y guía de instalación)

## Requirements

### Requirement 1: Interfaz Web Local

**User Story:** Como usuario, quiero acceder a la aplicación a través de un navegador web en mi máquina local, para poder ofuscar datos sensibles en PDFs sin enviar información a servidores externos.

#### Acceptance Criteria

1. THE Sistema SHALL proveer una interfaz web accesible desde el navegador en localhost en el puerto 3000 por defecto
2. THE Sistema SHALL utilizar el framework Cloudscape para todos los componentes de la interfaz de usuario
3. THE Sistema SHALL presentar todos los textos, etiquetas, mensajes y elementos de la interfaz en idioma español
4. THE Sistema SHALL ejecutarse completamente en la máquina local sin realizar conexiones de red externas durante el procesamiento de PDFs
5. IF el puerto por defecto se encuentra ocupado, THEN THE Sistema SHALL mostrar un mensaje de error indicando el conflicto de puerto y sugerir un puerto alternativo
6. WHEN el Sistema está listo para recibir solicitudes, THE Sistema SHALL mostrar en la terminal la URL completa de acceso (incluyendo puerto) para que el Usuario pueda abrirla en el navegador

### Requirement 2: Selección de Carpeta de PDFs

**User Story:** Como usuario, quiero indicar la ruta de una carpeta que contiene archivos PDF, para que la aplicación procese todos los PDFs dentro de ella.

#### Acceptance Criteria

1. THE Sistema SHALL proveer un campo de entrada de texto donde el Usuario ingrese la ruta de la Carpeta_Origen, aceptando rutas de hasta 260 caracteres en Windows y hasta 1024 caracteres en macOS
2. WHEN el Usuario confirma la ruta ingresada mediante un botón de acción, THE Sistema SHALL validar la ruta y listar todos los archivos con extensión `.pdf` (sin distinguir mayúsculas de minúsculas) encontrados en el nivel superior de la Carpeta_Origen, mostrando para cada archivo su nombre y tamaño
3. IF la ruta proporcionada no existe, no es un directorio, o el Sistema no tiene permisos de lectura sobre ella, THEN THE Sistema SHALL mostrar un mensaje de error en español indicando la causa específica (ruta inexistente, no es directorio, o sin permisos de lectura)
4. IF la Carpeta_Origen no contiene archivos con extensión `.pdf` en su nivel superior, THEN THE Sistema SHALL informar al Usuario que no se encontraron archivos PDF en la carpeta indicada

### Requirement 3: Detección de Datos Sensibles

**User Story:** Como usuario, quiero que la aplicación detecte automáticamente datos sensibles en los PDFs, para poder ofuscarlos sin revisión manual de cada documento.

#### Acceptance Criteria

1. THE Motor_NER SHALL ejecutarse completamente en la máquina local sin requerir conexión a internet
2. THE Sistema SHALL detectar los siguientes Tipo_Dato_Sensible por defecto: Nombre y Apellido, Email, Celular, Teléfono, Dirección, Tarjeta de Crédito, Número de Cuenta Bancaria, DNI, CUIT/CUIL, Pasaporte
3. THE Motor_NER SHALL reconocer formatos de datos específicos de Argentina: DNI con formato XX.XXX.XXX o XXXXXXXX (7 u 8 dígitos), números de teléfono con prefijo +54 seguido de 10 dígitos, y CUIT/CUIL con formato XX-XXXXXXXX-X (11 dígitos)
4. WHEN el Motor_NER detecta un dato sensible con un nivel de confianza igual o superior a 0.70 en el contenido del PDF, THE Sistema SHALL clasificarlo según su Tipo_Dato_Sensible correspondiente
5. IF el Motor_NER no detecta ningún Dato_Sensible en un archivo PDF, THEN THE Sistema SHALL informar al Usuario que no se encontraron datos sensibles en dicho archivo y continuar con el siguiente archivo de la cola de procesamiento
6. IF un dato detectado coincide con más de un Tipo_Dato_Sensible, THEN THE Sistema SHALL asignar el tipo con mayor nivel de confianza

### Requirement 4: Configuración de Tipos de Datos Sensibles

**User Story:** Como usuario, quiero poder configurar qué tipos de datos sensibles se detectan y ofuscan, para adaptar la herramienta a mis necesidades específicas.

#### Acceptance Criteria

1. THE Sistema SHALL proveer una interfaz de configuración donde el Usuario pueda activar o desactivar individualmente cada Tipo_Dato_Sensible mediante controles de tipo toggle
2. THE Sistema SHALL cargar la Configuración_Tipos por defecto con todos los tipos activos: NOMBRE, EMAIL, CELULAR, TELEFONO, DIRECCION, TARJETA_CREDITO, CUENTA_BANCARIA, DNI, PASAPORTE
3. WHEN el Usuario desactiva un Tipo_Dato_Sensible, THE Sistema SHALL omitir la detección y ofuscación de ese tipo en el siguiente procesamiento iniciado después del cambio
4. WHEN el Usuario reactiva un Tipo_Dato_Sensible previamente desactivado, THE Sistema SHALL incluir la detección y ofuscación de ese tipo en el siguiente procesamiento iniciado después del cambio
5. THE Sistema SHALL persistir la Configuración_Tipos en almacenamiento local de forma que se conserve entre sesiones de uso
6. IF la Configuración_Tipos no puede ser leída o se encuentra corrupta al iniciar la aplicación, THEN THE Sistema SHALL cargar la configuración por defecto con todos los tipos activos y mostrar un mensaje informativo al Usuario indicando que se restauró la configuración por defecto
7. IF el Usuario intenta desactivar todos los Tipo_Dato_Sensible, THEN THE Sistema SHALL mantener al menos un tipo activo e informar al Usuario que debe existir al menos 1 tipo activo para realizar el procesamiento

### Requirement 5: Ofuscación de Datos en PDFs

**User Story:** Como usuario, quiero que los datos sensibles detectados sean reemplazados por etiquetas descriptivas, para que el documento resultante no contenga información personal pero indique qué tipo de dato fue removido.

#### Acceptance Criteria

1. WHEN el Sistema detecta un Dato_Sensible de un Tipo_Dato_Sensible activo, THE Sistema SHALL reemplazar cada ocurrencia del texto del dato por la Etiqueta_Ofuscación correspondiente en formato `[TIPO]`
2. THE Sistema SHALL utilizar las siguientes Etiqueta_Ofuscación: `[NOMBRE]`, `[EMAIL]`, `[CELULAR]`, `[TELEFONO]`, `[DIRECCION]`, `[TARJETA_CREDITO]`, `[CUENTA_BANCARIA]`, `[DNI]`, `[PASAPORTE]`
3. THE Sistema SHALL preservar el formato original del PDF (estructura de páginas, imágenes, tablas y elementos no textuales) modificando únicamente el texto de los datos sensibles detectados, sin alterar el número de páginas ni eliminar contenido no sensible
4. IF el Sistema no puede procesar un archivo PDF (corrupto o protegido con contraseña), THEN THE Sistema SHALL registrar el error en el Registro_Log indicando el nombre del archivo y el motivo de fallo, notificar al Usuario en la interfaz que el archivo no pudo ser procesado, y continuar con el siguiente archivo
5. THE Sistema SHALL generar el PDF ofuscado como un archivo nuevo en la Carpeta_Ofuscados con el sufijo `_ofuscado` agregado al nombre original del archivo (ej: `mipdf.pdf` genera `ofuscados/mipdf_ofuscado.pdf`), preservando el archivo PDF original sin modificaciones en su ubicación original dentro de la Carpeta_Origen
6. WHEN el Sistema procesa un PDF con múltiples datos sensibles del mismo Tipo_Dato_Sensible, THE Sistema SHALL reemplazar cada ocurrencia de forma independiente con la misma Etiqueta_Ofuscación correspondiente

### Requirement 6: Ejecución 100% Local con Modelo de IA

**User Story:** Como usuario, quiero que toda la funcionalidad de detección de datos sensibles se ejecute localmente, para garantizar que ningún dato personal salga de mi máquina.

#### Acceptance Criteria

1. THE Instalador SHALL descargar el modelo de IA necesario para el Motor_NER durante la instalación inicial y verificar la integridad del archivo descargado mediante checksum antes de marcarlo como disponible
2. THE Motor_NER SHALL procesar los documentos sin realizar llamadas a APIs externas o servicios en la nube, sin abrir conexiones de red salientes durante la fase de detección y ofuscación
3. THE Sistema SHALL almacenar el modelo de IA localmente en el directorio de la aplicación y verificar que el modelo es cargable al iniciar la aplicación
4. THE Sistema SHALL funcionar sin conexión a internet una vez completada la instalación, incluyendo la carga del modelo, la detección de datos sensibles y la generación de PDFs ofuscados
5. IF la descarga del modelo de IA falla durante la instalación (por error de red, espacio insuficiente en disco o interrupción), THEN THE Instalador SHALL mostrar un mensaje de error indicando la causa de la falla y proveer instrucciones para reintentar la descarga

### Requirement 7: Instaladores Multiplataforma

**User Story:** Como usuario, quiero un script de instalación automática para mi sistema operativo, para poder configurar la aplicación con todas sus dependencias sin intervención manual.

#### Acceptance Criteria

1. THE Instalador SHALL proveer un archivo `setup.sh` para sistemas macOS que instale las dependencias del sistema, las dependencias de la aplicación, el modelo de IA local y configure la estructura de directorios del proyecto
2. THE Instalador SHALL proveer un archivo `setup.bat` para sistemas Windows que instale las dependencias del sistema, las dependencias de la aplicación, el modelo de IA local y configure la estructura de directorios del proyecto
3. WHEN el Usuario ejecuta el Instalador, THE Instalador SHALL verificar que los prerequisitos mínimos del sistema están presentes (versión de Python, espacio en disco disponible y permisos de escritura en el directorio de instalación) antes de iniciar la instalación de componentes
4. WHEN el Instalador completa la instalación de todos los componentes sin errores, THE Instalador SHALL mostrar un mensaje de confirmación indicando que la instalación finalizó exitosamente y que la aplicación está lista para ejecutarse
5. IF una dependencia no puede ser instalada, THEN THE Instalador SHALL mostrar un mensaje de error indicando el nombre de la dependencia que falló, la causa del fallo reportada por el gestor de paquetes y al menos un paso de resolución manual que el Usuario pueda seguir
6. IF el Instalador detecta que una dependencia ya se encuentra instalada en la versión requerida, THEN THE Instalador SHALL omitir la reinstalación de esa dependencia y continuar con el siguiente componente

### Requirement 8: Registro de Auditoría (Logging)

**User Story:** Como usuario, quiero un registro detallado de cada archivo procesado, para tener trazabilidad de las operaciones de ofuscación realizadas.

#### Acceptance Criteria

1. WHEN el Sistema procesa un archivo PDF, THE Sistema SHALL crear un Registro_Log con: nombre del archivo, tamaño del archivo en bytes, nombre del usuario del sistema operativo que ejecutó la operación, fecha y hora de procesamiento, resultado de la operación (éxito o error), y cantidad de datos sensibles detectados y ofuscados
2. THE Sistema SHALL almacenar los registros de log en un archivo persistente en formato estructurado legible (un registro por línea) dentro de la Carpeta_Log
3. THE Sistema SHALL mostrar el historial de registros de log en la interfaz web ordenados del más reciente al más antiguo, mostrando un máximo de 100 registros por página
4. THE Sistema SHALL registrar la fecha y hora en formato ISO 8601 con zona horaria local
5. IF el Sistema no puede escribir en el archivo de log, THEN THE Sistema SHALL mostrar una advertencia al Usuario en la interfaz web y continuar con el procesamiento del PDF sin interrumpir la operación

### Requirement 9: Compatibilidad Multiplataforma

**User Story:** Como usuario, quiero que la aplicación funcione tanto en Windows como en macOS, para poder usarla independientemente de mi sistema operativo.

#### Acceptance Criteria

1. THE Sistema SHALL ejecutarse en sistemas operativos Windows 10 o superior, iniciando el servidor local y sirviendo la interfaz web sin errores
2. THE Sistema SHALL ejecutarse en sistemas operativos macOS 12 (Monterey) o superior, iniciando el servidor local y sirviendo la interfaz web sin errores
3. THE Sistema SHALL manejar rutas de archivos que contengan espacios, caracteres acentuados (á, é, í, ó, ú, ñ) y separadores de ruta nativos del sistema operativo (backslash en Windows, forward slash en macOS) sin errores de lectura ni escritura
4. THE Sistema SHALL detectar automáticamente el sistema operativo y utilizar separadores de ruta nativos, codificación de caracteres del sistema de archivos local y comandos de sistema apropiados para la plataforma detectada
5. IF la ruta de la Carpeta_Origen o del archivo de salida excede 260 caracteres en Windows o 1024 caracteres en macOS, THEN THE Sistema SHALL mostrar un mensaje de error indicando que la ruta excede el límite permitido por el sistema operativo

### Requirement 10: Estructura de Carpetas de Salida

**User Story:** Como usuario, quiero que la aplicación organice los archivos generados en carpetas separadas (logs y PDFs ofuscados), para mantener orden en el proyecto y no mezclar archivos originales con los procesados.

#### Acceptance Criteria

1. THE Sistema SHALL crear y utilizar una carpeta `log/` dentro del directorio de la aplicación para almacenar todos los archivos de registro de auditoría
2. THE Sistema SHALL crear y utilizar una carpeta `ofuscados/` dentro del directorio de la aplicación para almacenar todos los PDFs ofuscados generados
3. WHEN el Sistema inicia por primera vez y las carpetas `log/` u `ofuscados/` no existen, THE Sistema SHALL crear ambas carpetas automáticamente antes de iniciar cualquier procesamiento
4. THE Sistema SHALL preservar los archivos PDF originales sin modificaciones en su ubicación original dentro de la Carpeta_Origen, sin mover, renombrar ni alterar su contenido
5. THE Sistema SHALL nombrar cada archivo PDF ofuscado agregando el sufijo `_ofuscado` al nombre original del archivo antes de la extensión (ej: `mipdf.pdf` se convierte en `mipdf_ofuscado.pdf`)
6. IF el Sistema no tiene permisos de escritura para crear o escribir en las carpetas `log/` u `ofuscados/`, THEN THE Sistema SHALL mostrar un mensaje de error al Usuario indicando la carpeta afectada y el permiso faltante, sin iniciar el procesamiento de archivos

### Requirement 11: Carpeta de Test con PDFs de Ejemplo

**User Story:** Como desarrollador, quiero disponer de una carpeta de test con archivos PDF de ejemplo que contengan datos sensibles ficticios argentinos, para poder verificar que la ofuscación funciona correctamente sin usar datos reales.

#### Acceptance Criteria

1. THE Sistema SHALL incluir una carpeta `test/` dentro del directorio de la aplicación destinada a almacenar archivos PDF de prueba
2. THE Sistema SHALL proveer 3 archivos PDF de ejemplo dentro de la Carpeta_Test, cada uno conteniendo datos sensibles ficticios en formato argentino
3. THE Sistema SHALL incluir en los PDFs de ejemplo los siguientes tipos de datos sensibles ficticios: nombres y apellidos argentinos, números de DNI (formato XX.XXX.XXX y XXXXXXXX), direcciones de email, números de teléfono con prefijo +54, direcciones postales argentinas, números de CUIT/CUIL (formato XX-XXXXXXXX-X) y números de pasaporte
4. THE Sistema SHALL generar cada PDF de ejemplo con contenido textual diferente que simule documentos reales (formulario de registro, contrato de servicio y ficha de empleado) para cubrir distintos escenarios de detección
5. THE Sistema SHALL utilizar exclusivamente datos ficticios que no correspondan a personas reales en los PDFs de ejemplo, evitando cualquier coincidencia con información personal identificable real
6. WHEN el Usuario ejecuta el procesamiento de ofuscación sobre la Carpeta_Test, THE Sistema SHALL detectar y ofuscar todos los datos sensibles ficticios presentes en los 3 PDFs de ejemplo sin errores
7. IF la Carpeta_Test no existe al iniciar la aplicación, THEN THE Sistema SHALL crear la carpeta `test/` automáticamente junto con las demás carpetas de la estructura del proyecto

### Requirement 12: Documentación del Proyecto

**User Story:** Como usuario o desarrollador, quiero disponer de documentación completa del proyecto organizada en una carpeta dedicada, para entender la arquitectura, aprender a usar la aplicación y poder instalarla sin asistencia externa.

#### Acceptance Criteria

1. THE Sistema SHALL incluir una carpeta `documentacion/` dentro del directorio de la aplicación destinada a almacenar toda la documentación del proyecto
2. THE Sistema SHALL proveer un documento de arquitectura del sistema dentro de la Carpeta_Documentacion que describa: los componentes principales de la aplicación, las tecnologías utilizadas, el flujo de procesamiento de PDFs y el diagrama de estructura de carpetas del proyecto
3. THE Sistema SHALL proveer una guía de usuario dentro de la Carpeta_Documentacion que describa: cómo iniciar la aplicación, cómo seleccionar una carpeta de PDFs, cómo configurar los tipos de datos sensibles, cómo ejecutar el procesamiento de ofuscación y cómo consultar los registros de auditoría
4. THE Sistema SHALL proveer una guía de instalación dentro de la Carpeta_Documentacion que describa: los prerequisitos del sistema (versión de Python, sistema operativo compatible), los pasos para ejecutar el Instalador en macOS y Windows, la verificación de la instalación correcta y los pasos de resolución de problemas comunes
5. THE Sistema SHALL redactar toda la documentación en idioma español, utilizando terminología consistente con el Glossary definido en este documento de requerimientos
6. IF la Carpeta_Documentacion no existe al iniciar la aplicación, THEN THE Sistema SHALL crear la carpeta `documentacion/` automáticamente junto con las demás carpetas de la estructura del proyecto
7. THE Sistema SHALL mantener la documentación en formato Markdown (.md) para facilitar su lectura tanto en editores de texto como en plataformas de repositorios de código
