# Ollama - Instalación y uso del modelo LLM

## Requisitos previos

- Tener [Ollama](https://ollama.com/) instalado en tu sistema.
- En Windows, descargar el instalador desde https://ollama.com/download/windows

## Descargar el modelo Llama 3.1 8B

Abrir una terminal (CMD o PowerShell) y ejecutar:

```bash
ollama pull llama3.1:8b
```

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
