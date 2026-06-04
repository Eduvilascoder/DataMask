# Ollama - Instalación y uso del modelo LLM

## Requisitos previos

- Tener [Ollama](https://ollama.com/) instalado en tu sistema.
- En Windows, descargar el instalador desde https://ollama.com/download/windows

## Descargar un modelo

DataMask usa `llama3.1:8b` por defecto, pero el modelo es configurable desde la
página de Configuración de la app (incluso podés descargar uno nuevo desde ahí).

Para descargar el modelo por defecto desde terminal:

```bash
ollama pull llama3.1:8b
```

Otros modelos recomendados para NER (livianos):

```bash
ollama pull qwen2.5:7b    # ~4.7 GB
ollama pull qwen2.5:3b    # ~1.9 GB
```

> ⚠️ Evitá modelos de 14B+ parámetros (ej: `qwen3.6` de ~23GB) en máquinas con
> poca RAM: pueden congelar el sistema. Usá modelos de ≤8B salvo que tengas 32GB+.

## Iniciar el servidor de Ollama

```bash
ollama serve
```

> El servidor queda escuchando en `http://localhost:11434` por defecto.

## Verificar que funciona

```bash
ollama run llama3.1:8b "Hola"
```

## Notas

- El modelo Llama 3.1 8B requiere aproximadamente 4.7 GB de RAM.
- La primera vez que se ejecuta `ollama pull` descarga el modelo completo, puede tardar según la conexión.
- El servidor (`ollama serve`) debe estar corriendo para que la aplicación DataMask pueda comunicarse con el modelo.
- Si el puerto 11434 está ocupado, Ollama fallará al iniciar. Verificar con `netstat -an | findstr 11434` en Windows.
- El modelo activo, la temperatura y el keep_alive se configuran en `config/ollama.json` (o desde la página de Configuración de la app).
- Para listar los modelos instalados: `ollama list`.
