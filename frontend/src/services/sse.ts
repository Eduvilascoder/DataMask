import type { ProgressEvent } from '../types';

const SSE_URL = '/api/process/status';

export type ProgressCallback = (event: ProgressEvent) => void;
export type CompleteCallback = (data: any) => void;
export type ErrorCallback = (error: string) => void;

/**
 * Crea una conexión SSE para recibir actualizaciones de progreso
 * del procesamiento de PDFs en tiempo real.
 *
 * Escucha eventos nombrados del backend:
 * - file_start: inicio de procesamiento de un archivo
 * - file_complete: archivo procesado exitosamente
 * - file_error: error al procesar un archivo
 * - complete: procesamiento finalizado
 * - error: error fatal
 *
 * @returns Función para cerrar la conexión.
 */
export function connectToProgress(
  onProgress: ProgressCallback,
  onError: ErrorCallback
): () => void {
  const eventSource = new EventSource(SSE_URL);
  let hasReceivedEvent = false;

  const handleEvent = (eventType: string) => (event: MessageEvent) => {
    hasReceivedEvent = true;
    try {
      const data = JSON.parse(event.data);
      onProgress({
        type: eventType,
        ...data,
      } as ProgressEvent);

      if (eventType === 'complete' || eventType === 'error') {
        eventSource.close();
      }
    } catch {
      // Ignore parse errors
    }
  };

  // Escuchar todos los tipos de eventos que emite el backend
  eventSource.addEventListener('file_start', handleEvent('file_start'));
  eventSource.addEventListener('file_complete', handleEvent('file_complete'));
  eventSource.addEventListener('file_error', handleEvent('file_error'));
  eventSource.addEventListener('complete', handleEvent('complete'));
  eventSource.addEventListener('error', handleEvent('error'));

  // El onerror de EventSource se dispara en reconexiones normales.
  // Solo reportar error si nunca recibimos un evento (conexión fallida real).
  eventSource.onerror = () => {
    // EventSource.CLOSED = 2
    if (eventSource.readyState === 2) {
      if (!hasReceivedEvent) {
        onError('Se perdió la conexión con el servidor.');
      }
      eventSource.close();
    }
    // Si readyState es CONNECTING (0), EventSource está reintentando — no es un error fatal
  };

  return () => {
    eventSource.close();
  };
}
