---
inclusion: always
---

# Flujo de desarrollo — DataMask

## Reinicio tras cambios de código

Después de CUALQUIER cambio en el código backend (Python) o en `config/*.json`,
SIEMPRE matar todos los procesos y relanzar la app limpia. El motor NER se
mantiene como singleton en memoria (`_ner_engine` en `app/api/routes.py`), por
lo que un `--reload` de uvicorn no siempre recrea el singleton con la config
actualizada.

Pasos obligatorios tras un cambio:

1. Matar todos los procesos:
   ```bash
   pkill -9 -f uvicorn
   ```
2. Confirmar que el puerto 3000 quedó libre:
   ```bash
   lsof -ti :3000 || echo "PUERTO LIBRE"
   ```
3. Relanzar la app:
   ```bash
   .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 3000 --reload
   ```
4. Verificar health:
   ```bash
   curl -s http://localhost:3000/api/health
   ```

## Build del frontend

Si el cambio toca el frontend (`frontend/src/**`), rebuildar antes de probar:
```bash
cd frontend && npm run build
```
El backend sirve el build desde `frontend/build/`. El `--reload` de uvicorn
detecta el nuevo build al reiniciar.

## Sincronización con GitHub

El repositorio remoto es `https://github.com/Eduvilascoder/DataMask.git`.
GitDefender ya está aprobado. El build del frontend no se commitea (está en
`.gitignore`).
