# Bugfix Requirements Document

## Introduction

El sistema de ofuscación de datos sensibles en PDFs no detecta tres categorías de datos personales que aparecen frecuentemente en documentos variados (estados de cuenta bancarios, facturas de servicios, contratos, documentos legales, etc.):

1. **Fechas** en múltiples formatos — no existe el tipo `FECHA` en el enum `SensitiveDataType`, no hay patrón regex para fechas, y aunque el prompt de Ollama menciona `FECHAS` como tipo válido, no hay mapeo funcional en el sistema para procesarlo. Las fechas pueden revelar información sensible como fechas de nacimiento, fechas de vencimiento de documentos, y fechas de transacciones financieras.
2. **Números de cuenta** en formatos no-CBU — el único regex de cuenta bancaria cubre CBU de 22 dígitos consecutivos, pero no cubre formatos de cuenta/tarjeta con grupos separados por guiones u otros separadores, comunes en extractos de American Express, Visa, Mastercard y otros emisores.
3. **Direcciones** en formatos argentinos abreviados y variados — la detección semántica (Ollama/spaCy) no reconoce formatos típicos de extractos bancarios, facturas de servicios y documentos administrativos donde las direcciones usan abreviaturas, formatos compactos o puntuación irregular.

Dado que el sistema procesará todo tipo de documento, los patrones deben ser lo suficientemente amplios para cubrir variantes comunes sin generar falsos positivos excesivos.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN el texto contiene fechas en formato DD/MM/AA (ej: `30/06/25`, `22/06/25`) THEN el sistema no las detecta ni las ofusca porque no existe el tipo `FECHA` en `SensitiveDataType` ni un patrón regex correspondiente.

1.2 WHEN el texto contiene fechas en formato DD/MM/AAAA (ej: `04/08/2025`, `15/03/1990`) THEN el sistema no las detecta ni las ofusca por la misma ausencia del tipo y patrón regex.

1.3 WHEN el texto contiene fechas en formato AAAA-MM-DD (ISO 8601, ej: `2025-08-04`, `1990-03-15`) THEN el sistema no las detecta ni las ofusca.

1.4 WHEN el texto contiene fechas en formato textual con mes abreviado o completo (ej: `4 de agosto de 2025`, `15-Mar-2025`, `Jun 2025`) THEN el sistema no las detecta ni las ofusca.

1.5 WHEN el texto contiene fechas separadas por guiones en formato DD-MM-AAAA o DD-MM-AA (ej: `04-08-2025`, `30-06-25`) THEN el sistema no las detecta ni las ofusca.

1.6 WHEN el texto contiene un número de cuenta en formato grupos separados por guiones (ej: `3764-575886-12000`) THEN el sistema no lo detecta porque el regex de `CUENTA_BANCARIA` solo cubre CBU de exactamente 22 dígitos consecutivos.

1.7 WHEN el texto contiene un número de cuenta en formato con espacios o puntos como separadores (ej: `3764 575886 12000`, `0720.1234.5678.9012`) THEN el sistema no lo detecta.

1.8 WHEN el texto contiene direcciones en formato abreviado de extracto bancario (ej: `GRANADEROS 457 5 G`) THEN el sistema no las detecta porque la detección semántica no reconoce estos formatos.

1.9 WHEN el texto contiene direcciones con abreviaturas y formato de factura (ej: `FLORES AVELLANEDA ,AV. Y ARANGUREN DR JU`) THEN el sistema no las detecta.

1.10 WHEN el texto contiene direcciones con código postal (ej: `Av. Rivadavia 1234 (C1033AAJ)`, `Mitre 567, CP 5000`) THEN el sistema no las detecta de forma completa.

1.11 WHEN Ollama detecta una entidad con tipo `FECHAS` THEN el sistema no la procesa correctamente porque `FECHAS` no está en el mapeo `known_types` de `ollama_client.py` y no tiene un `SensitiveDataType` correspondiente en el enum.

### Expected Behavior (Correct)

2.1 WHEN el texto contiene fechas en formato DD/MM/AA (ej: `30/06/25`, `22/06/25`) THEN el sistema SHALL detectarlas mediante un patrón regex y ofuscarlas con el placeholder `[FECHA]`.

2.2 WHEN el texto contiene fechas en formato DD/MM/AAAA (ej: `04/08/2025`, `15/03/1990`) THEN el sistema SHALL detectarlas mediante un patrón regex y ofuscarlas con el placeholder `[FECHA]`.

2.3 WHEN el texto contiene fechas en formato AAAA-MM-DD (ISO 8601, ej: `2025-08-04`) THEN el sistema SHALL detectarlas mediante un patrón regex y ofuscarlas con el placeholder `[FECHA]`.

2.4 WHEN el texto contiene fechas en formato textual con mes en español (ej: `4 de agosto de 2025`, `15 de marzo de 1990`) THEN el sistema SHALL detectarlas mediante un patrón regex y ofuscarlas con el placeholder `[FECHA]`.

2.5 WHEN el texto contiene fechas separadas por guiones DD-MM-AAAA o DD-MM-AA (ej: `04-08-2025`, `30-06-25`) THEN el sistema SHALL detectarlas mediante un patrón regex y ofuscarlas con el placeholder `[FECHA]`.

2.6 WHEN el texto contiene un número de cuenta en formato grupos separados por guiones (ej: `3764-575886-12000`) THEN el sistema SHALL detectarlo mediante un patrón regex y ofuscarlo con el placeholder `[CUENTA_BANCARIA]`.

2.7 WHEN el texto contiene un número de cuenta en formato con espacios o puntos como separadores (ej: `3764 575886 12000`) THEN el sistema SHALL detectarlo mediante un patrón regex y ofuscarlo con el placeholder `[CUENTA_BANCARIA]`.

2.8 WHEN el texto contiene direcciones en formato abreviado de extracto bancario (ej: `GRANADEROS 457 5 G`) THEN el sistema SHALL detectarlas mediante un patrón regex de dirección argentina y ofuscarlas con el placeholder `[DIRECCION]`.

2.9 WHEN el texto contiene direcciones con abreviaturas y formato de factura (ej: `FLORES AVELLANEDA ,AV. Y ARANGUREN DR JU`) THEN el sistema SHALL detectarlas mediante un patrón regex de dirección argentina y ofuscarlas con el placeholder `[DIRECCION]`.

2.10 WHEN el texto contiene direcciones con código postal (ej: `Av. Rivadavia 1234 (C1033AAJ)`) THEN el sistema SHALL detectarlas de forma completa incluyendo el código postal y ofuscarlas con el placeholder `[DIRECCION]`.

2.11 WHEN Ollama detecta una entidad con tipo `FECHAS` THEN el sistema SHALL mapearla correctamente al tipo `FECHA` interno y procesarla como dato sensible a ofuscar.

### Unchanged Behavior (Regression Prevention)

3.1 WHEN el texto contiene un DNI en formato `XX.XXX.XXX` o `XXXXXXXX` THEN el sistema SHALL CONTINUE TO detectarlo y ofuscarlo con el placeholder `[DNI]`.

3.2 WHEN el texto contiene un email en formato estándar THEN el sistema SHALL CONTINUE TO detectarlo y ofuscarlo con el placeholder `[EMAIL]`.

3.3 WHEN el texto contiene un número de teléfono con prefijo internacional THEN el sistema SHALL CONTINUE TO detectarlo y ofuscarlo con el placeholder `[TELEFONO]`.

3.4 WHEN el texto contiene un CBU de 22 dígitos THEN el sistema SHALL CONTINUE TO detectarlo y ofuscarlo con el placeholder `[CUENTA_BANCARIA]`.

3.5 WHEN el texto contiene un número de tarjeta de crédito de 16 dígitos agrupados de a 4 THEN el sistema SHALL CONTINUE TO detectarlo y ofuscarlo con el placeholder `[TARJETA_CREDITO]`.

3.6 WHEN el texto contiene un CUIT/CUIL en formato estándar THEN el sistema SHALL CONTINUE TO detectarlo y ofuscarlo con el placeholder `[CUIT_CUIL]`.

3.7 WHEN el texto contiene un nombre propio detectado por Ollama o la heurística de mayúsculas THEN el sistema SHALL CONTINUE TO detectarlo y ofuscarlo con el placeholder `[NOMBRE]`.

3.8 WHEN el texto contiene una dirección detectada semánticamente por Ollama (formato completo como `Av. Corrientes 1234, Buenos Aires`) THEN el sistema SHALL CONTINUE TO detectarla y ofuscarla con el placeholder `[DIRECCION]`.

3.9 WHEN un número es parte de un monto monetario (ej: `$1.234,56`, `USD 500.00`) THEN el sistema SHALL CONTINUE TO no ofuscarlo — no debe generar falsos positivos con los nuevos regex de fechas o cuentas.

3.10 WHEN un número es un porcentaje, código de referencia, o número de página (ej: `15%`, `REF: 12345`, `Pág. 3`) THEN el sistema SHALL CONTINUE TO no ofuscarlo.

3.11 WHEN el texto contiene números que forman parte de una dirección ya detectada (ej: el `457` en `GRANADEROS 457`) THEN el sistema SHALL CONTINUE TO no detectar esos números individualmente como DNI u otro tipo — la entidad dirección tiene prioridad.
