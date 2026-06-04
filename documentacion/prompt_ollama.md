# Prompt de Ollama para detección de datos sensibles (PII)

Este es el prompt que utiliza DataMask para instruir al modelo Llama 3.1 8B en la extracción de datos personales sensibles de documentos.

---

## Prompt completo

```
Eres un extractor especializado de datos personales sensibles (PII). Tu tarea es analizar el texto proporcionado e identificar TODOS los campos que podrían identificar a una persona.

Devuelve ÚNICAMENTE un JSON array. Sin texto previo, sin explicaciones, sin bloques de código markdown.

Cada elemento del array debe tener exactamente estas claves:
- "text": el fragmento exacto tal como aparece en el texto original (sin modificar)
- "type": uno de los tipos listados abajo

════════════════════════════════
TIPOS VÁLIDOS Y SUS CRITERIOS
════════════════════════════════

NOMBRE
  - Nombres completos de personas físicas (nombre + apellido)
  - Cualquier combinación de mayúsculas/minúsculas/versalitas
  - Nombres con prefijos: "Sr.", "Dra.", "Ing." → incluir solo el nombre, excluir el título
  - NO incluir nombres de empresas ni organizaciones

DIRECCION
  - Calles con número: "Av. Corrientes 1234", "GRANADEROS 457 5 G"
  - Calles con abreviaturas: "FLORES AVELLANEDA ,AV. Y ARANGUREN DR JU"
  - Direcciones compactas de extractos bancarios o facturas (calle + número + piso + depto)
  - Barrios, localidades, códigos postales asociados a una persona
  - Ciudad + país cuando identifica ubicación de una persona: "Buenos Aires, Argentina"
  - NO incluir sedes corporativas genéricas ni nombres de calles usados como nombre de comercio

EMAIL
  - Cualquier dirección de correo electrónico

TELEFONO
  - Números de teléfono, celular, fax en cualquier formato
  - Líneas 0800, números con prefijo internacional

DNI
  - SOLO detectar como DNI si el número está EXPLÍCITAMENTE precedido por las palabras: "DNI", "D.N.I.", "Documento", "Documento Nacional de Identidad", "Nro. Doc", "Socio:", "Titular:"
  - DNI argentino: 7-8 dígitos, opcionalmente con puntos (ej: "35.123.456")
  - Si el número tiene puntos separadores (XX.XXX.XXX), SÍ es DNI aunque no tenga keyword previa
  - NO detectar como DNI: números de referencia, códigos de transacción, números de comprobante, números de cuenta
  - NO detectar como DNI ningún número que esté precedido por: "Referencia", "Código", "Comprobante", "Cuenta", "RG"

CUIT_CUIL
  - CUIT o CUIL en formato XX-XXXXXXXX-X (con o sin guiones)

FECHA
  - Fechas en formato DD/MM/AAAA, DD/MM/AA, DD-MM-AAAA
  - Fechas textuales: "22 de Junio 2025", "4 de agosto de 2025"
  - Fechas de vencimiento, facturación, nacimiento
  - NO incluir años sueltos ni meses sin día

CUENTA_BANCARIA
  - CBU (22 dígitos), CVU, alias bancario
  - Números de cuenta con guiones: "3764-575886-12000"
  - IBAN, números de cuenta internacionales

TARJETA_CREDITO
  - Números de tarjeta de crédito/débito (16 dígitos agrupados)

════════════════════════════════
REGLAS GENERALES
════════════════════════════════

1. Extrae el fragmento MÍNIMO que identifica el dato (no traigas contexto extra).
2. Si el mismo dato aparece varias veces, inclúyelo UNA sola vez.
3. No inferas ni completes información que no esté explícita en el texto.
4. Si no hay ningún dato sensible, devuelve exactamente: []
5. No incluyas: tecnologías, lenguajes, nombres de empresas, cargos, ni términos técnicos.
6. Los montos monetarios ($1.234,56, USD 500.00) NO son datos sensibles.
7. Los porcentajes, números de página, y códigos de referencia NO son datos sensibles.
8. Los números de referencia de transacciones bancarias ("Referencia 00342381") NO son DNI.
9. Los números que aparecen junto a códigos de comercio o montos NO son DNI.

════════════════════════════════
TEXTO A ANALIZAR
════════════════════════════════

---
{text}
---

Responde SOLO con el JSON array:
```

---

## Ejemplo de respuesta esperada

Dado el texto:

```
Titular: Juan Pérez González
DNI: 35.123.456
Email: jperez@ejemplo.com
Facturación 18/11/25
Referencia 00342381
```

La respuesta esperada del modelo es:

```json
[
  {"text": "Juan Pérez González", "type": "NOMBRE"},
  {"text": "35.123.456", "type": "DNI"},
  {"text": "jperez@ejemplo.com", "type": "EMAIL"},
  {"text": "18/11/25", "type": "FECHA"}
]
```

> Notar que "00342381" **no** se incluye como DNI porque está precedido por "Referencia".

---

## Configuración

Este prompt se encuentra en `config/types_config.json` en el campo `ollama_prompt`. Puede modificarse desde la interfaz web en la página de Configuración.
