# Guía de Usuario

## Introducción

Esta guía describe cómo utilizar la aplicación de Ofuscación de Datos Sensibles en PDFs. La aplicación permite detectar y reemplazar automáticamente información personal identificable (nombres, DNI, emails, teléfonos, etc.) en archivos PDF, generando copias ofuscadas sin modificar los archivos originales.

---

## 1. Iniciar la Aplicación

### En macOS

Abra una terminal y ejecute desde el directorio del proyecto:

```bash
./run.sh
```

### En Windows

Abra una terminal (CMD o PowerShell) y ejecute desde el directorio del proyecto:

```cmd
run.bat
```

### Resultado esperado

Al iniciar correctamente, verá un mensaje similar a:

```
============================================================
  Ofuscación de Datos Sensibles en PDFs
============================================================

→ Iniciando servidor en http://localhost:3000
```

Abra su navegador web y acceda a la dirección indicada: **http://localhost:3000**

### Detener la aplicación

Para detener el servidor de DataMask:

**macOS:**
```bash
./stop.sh
```

**Windows:**
```cmd
stop.bat
```

Alternativamente, puede presionar `Ctrl+C` en la terminal donde se ejecuta el servidor.

> **Nota**: Si el puerto 3000 está ocupado por otra aplicación, el Sistema mostrará un mensaje de error indicando el conflicto. Puede cambiar el puerto configurando la variable de entorno `PORT` antes de ejecutar:
>
> ```bash
> PORT=3001 ./run.sh        # macOS
> set PORT=3001 && run.bat  # Windows
> ```

---

## 2. Seleccionar una Carpeta de PDFs

1. En la página principal de la aplicación, localice el campo de texto **"Ruta de la carpeta"**.

2. Ingrese la ruta completa de la Carpeta_Origen que contiene los archivos PDF que desea procesar.

   - **macOS**: ejemplo `/Users/miusuario/Documentos/contratos`
   - **Windows**: ejemplo `C:\Users\miusuario\Documentos\contratos`

3. Haga clic en el botón **"Validar"** (o presione Enter).

4. El Sistema validará la ruta y mostrará la lista de archivos PDF encontrados con su nombre y tamaño.

### Posibles mensajes de error

| Situación | Mensaje |
|-----------|---------|
| La ruta no existe | "La ruta especificada no existe" |
| La ruta no es un directorio | "La ruta especificada no es un directorio" |
| Sin permisos de lectura | "Sin permisos de lectura sobre la carpeta" |
| Sin archivos PDF | "No se encontraron archivos PDF en la carpeta indicada" |

> **Consejo**: La aplicación busca archivos con extensión `.pdf` sin distinguir mayúsculas de minúsculas (`.pdf`, `.PDF`, `.Pdf` son todos válidos). Solo se listan archivos en el nivel superior de la carpeta, no en subcarpetas.

---

## 3. Configurar Tipos de Datos Sensibles

Antes de ejecutar el procesamiento, puede personalizar qué tipos de datos sensibles desea detectar y ofuscar.

1. Navegue a la sección de **Configuración** en la aplicación.

2. Verá una lista de tipos de datos con controles de tipo toggle (activar/desactivar):

   | Tipo | Etiqueta de Ofuscación | Ejemplo detectado |
   |------|----------------------|-------------------|
   | Nombre y Apellido | `[NOMBRE]` | Juan Carlos Pérez |
   | Email | `[EMAIL]` | juan.perez@email.com |
   | Celular | `[CELULAR]` | +54 9 11 4567 8901 |
   | Teléfono | `[TELEFONO]` | +54 11 4567 8901 |
   | Dirección | `[DIRECCION]` | Av. Corrientes 1234, CABA |
   | Tarjeta de Crédito | `[TARJETA_CREDITO]` | 4532-1234-5678-9012 |
   | Cuenta Bancaria | `[CUENTA_BANCARIA]` | CBU 20-digit number |
   | DNI | `[DNI]` | 32.456.789 |
   | CUIT/CUIL | `[CUIT_CUIL]` | 20-32456789-4 |
   | Pasaporte | `[PASAPORTE]` | AAB123456 |

3. **Desactive** los tipos que no desea detectar haciendo clic en el toggle correspondiente.

4. **Reactive** los tipos que desea incluir nuevamente.

5. La configuración se guarda automáticamente y se conserva entre sesiones.

> **Importante**: Debe mantener al menos un tipo de dato sensible activo. Si intenta desactivar todos, el Sistema le informará que debe existir al menos 1 tipo activo.

---

## 4. Ejecutar el Procesamiento de Ofuscación

1. Una vez seleccionada la carpeta y configurados los tipos deseados, haga clic en el botón **"Procesar"** o **"Iniciar ofuscación"**.

2. El Sistema procesará cada archivo PDF de la lista:
   - Extrae el texto de cada página
   - Detecta datos sensibles según los tipos activos
   - Reemplaza cada dato detectado por su Etiqueta_Ofuscación correspondiente
   - Genera un nuevo PDF ofuscado

3. Durante el procesamiento, verá una **barra de progreso** que se actualiza en tiempo real mostrando:
   - Archivo actual siendo procesado
   - Cantidad de archivos completados vs. total
   - Cantidad de datos sensibles detectados

4. Al finalizar, se muestra un **resumen de resultados** con:
   - Total de archivos procesados exitosamente
   - Total de datos sensibles detectados y ofuscados
   - Archivos que no pudieron ser procesados (si los hay)

### Archivos que no pueden procesarse

Si un PDF está corrupto o protegido con contraseña, el Sistema:
- Registra el error en el log de auditoría
- Muestra una notificación en la interfaz
- Continúa con el siguiente archivo sin interrumpir el proceso

---

## 5. Consultar los Registros de Auditoría

La aplicación mantiene un registro detallado de cada operación de ofuscación realizada.

1. Navegue a la sección de **Logs** o **Registros** en la aplicación.

2. Verá una tabla con las siguientes columnas:

   | Campo | Descripción |
   |-------|-------------|
   | Archivo | Nombre del PDF procesado |
   | Tamaño | Tamaño del archivo en bytes |
   | Usuario | Usuario del sistema operativo que ejecutó la operación |
   | Fecha y hora | Timestamp en formato ISO 8601 con zona horaria local |
   | Resultado | "Éxito" o "Error" |
   | Entidades detectadas | Cantidad total de datos sensibles encontrados |

3. Los registros se muestran ordenados del más reciente al más antiguo, con un máximo de 100 registros por página.

4. Los archivos de log se almacenan de forma persistente en la carpeta `log/` del proyecto en formato JSON Lines (un registro por línea).

---

## 6. Entender la Salida

### Carpeta de salida: `ofuscados/`

Todos los PDFs ofuscados se generan dentro de la carpeta `ofuscados/` ubicada en el directorio raíz de la aplicación.

### Convención de nombres: sufijo `_ofuscado`

Cada archivo generado mantiene el nombre original con el sufijo `_ofuscado` antes de la extensión:

| Archivo original | Archivo ofuscado generado |
|-----------------|--------------------------|
| `contrato.pdf` | `ofuscados/contrato_ofuscado.pdf` |
| `ficha_empleado.pdf` | `ofuscados/ficha_empleado_ofuscado.pdf` |
| `formulario.PDF` | `ofuscados/formulario_ofuscado.pdf` |

### Qué esperar en el PDF ofuscado

- El formato del documento se preserva (páginas, imágenes, tablas, estructura)
- Solo el texto de datos sensibles detectados es reemplazado por etiquetas entre corchetes
- Los archivos originales **nunca se modifican** — permanecen intactos en su ubicación original

### Ejemplo de ofuscación

**Texto original en el PDF:**
```
Nombre: Juan Carlos Pérez
DNI: 32.456.789
Email: juan.perez@empresa.com
Teléfono: +54 11 4567 8901
```

**Texto en el PDF ofuscado:**
```
Nombre: [NOMBRE]
DNI: [DNI]
Email: [EMAIL]
Teléfono: [TELEFONO]
```

---

## Carpeta de Test

La aplicación incluye una carpeta `test/` con 3 archivos PDF de ejemplo que contienen datos sensibles ficticios en formato argentino. Puede usar esta carpeta para verificar que la ofuscación funciona correctamente antes de procesar documentos reales.

Para probar:
1. Ingrese la ruta de la carpeta `test/` del proyecto como Carpeta_Origen
2. Ejecute el procesamiento
3. Verifique los resultados en `ofuscados/`
