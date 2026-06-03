import React, { useEffect, useState, useRef, useCallback } from 'react';
import {
  ProgressBar,
  Container,
  Header,
  SpaceBetween,
  Box,
  Alert,
  KeyValuePairs,
  Button,
} from '@cloudscape-design/components';
import { connectToProgress } from '../services/sse';
import { useProcessing } from '../context/ProcessingContext';
import es from '../i18n/es';

interface ProcessingProgressProps {
  isActive: boolean;
  onComplete: () => void;
}

interface Summary {
  total: number;
  success: number;
  failed: number;
  totalEntities: number;
  elapsedMs: number;
  totalVolumeBytes: number;
  cancelled: boolean;
}

/** Formatea milisegundos a una representación legible. */
function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms} ms`;
  const seconds = Math.floor(ms / 1000);
  if (seconds < 60) return `${seconds}s`;
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  return `${minutes}m ${remainingSeconds}s`;
}

/** Formatea bytes a una representación legible. */
function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

const ProcessingProgress: React.FC<ProcessingProgressProps> = ({ isActive, onComplete }) => {
  const [percentage, setPercentage] = useState(0);
  const [currentFile, setCurrentFile] = useState('');
  const [currentIndex, setCurrentIndex] = useState(0);
  const [totalFiles, setTotalFiles] = useState(0);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [elapsedDisplay, setElapsedDisplay] = useState('0s');
  const [cancelling, setCancelling] = useState(false);
  const disconnectRef = useRef<(() => void) | null>(null);
  const timerIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const { startTimer, stopTimer, getElapsedMs } = useProcessing();

  // Timer que actualiza el display cada segundo
  useEffect(() => {
    if (isActive && !summary && !error) {
      timerIntervalRef.current = setInterval(() => {
        const elapsed = getElapsedMs();
        setElapsedDisplay(formatDuration(elapsed));
      }, 1000);
    }
    return () => {
      if (timerIntervalRef.current) {
        clearInterval(timerIntervalRef.current);
        timerIntervalRef.current = null;
      }
    };
  }, [isActive, summary, error, getElapsedMs]);

  const handleCancel = useCallback(async () => {
    setCancelling(true);
    try {
      await fetch('/api/process/cancel', { method: 'POST' });
    } catch {
      // Si falla, igual dejamos que el SSE maneje el estado
    }
  }, []);

  useEffect(() => {
    if (!isActive) return;

    setPercentage(0);
    setCurrentFile('');
    setSummary(null);
    setError(null);
    setCurrentIndex(0);
    setTotalFiles(0);
    setCancelling(false);
    startTimer();

    const disconnect = connectToProgress(
      (event: any) => {
        const type = event.type;

        if (type === 'file_start') {
          setCurrentFile(event.file || '');
          setCurrentIndex(event.index || 0);
          setTotalFiles(event.total || 0);
          const baseProgress = event.total > 0 ? (event.index / event.total) * 100 : 0;
          const stepSize = event.total > 0 ? (1 / event.total) * 100 : 0;
          const pct = Math.round(baseProgress + stepSize * 0.3);
          setPercentage(pct);
        }

        if (type === 'file_complete') {
          const pct = event.total > 0 ? Math.round(((event.index + 1) / event.total) * 100) : 100;
          setPercentage(pct);
        }

        if (type === 'file_error') {
          const pct = event.total > 0 ? Math.round(((event.index + 1) / event.total) * 100) : 100;
          setPercentage(pct);
        }

        if (type === 'complete') {
          setPercentage(100);
          stopTimer();
          const results = event.results || [];
          const totalEntities = results.reduce(
            (sum: number, r: any) => sum + (r.entities_found || 0), 0
          );
          setSummary({
            total: event.total || 0,
            success: event.success || 0,
            failed: event.failed || 0,
            totalEntities,
            elapsedMs: event.elapsed_ms || 0,
            totalVolumeBytes: event.total_volume_bytes || 0,
            cancelled: event.cancelled || false,
          });
          onComplete();
        }

        if (type === 'error') {
          stopTimer();
          setError(event.message || 'Error desconocido durante el procesamiento.');
          onComplete();
        }
      },
      (errorMsg: string) => {
        stopTimer();
        setError(errorMsg);
        onComplete();
      }
    );

    disconnectRef.current = disconnect;

    return () => {
      if (disconnectRef.current) {
        disconnectRef.current();
      }
    };
  }, [isActive, onComplete, startTimer, stopTimer]);

  if (!isActive && !summary && !error) return null;

  return (
    <Container header={<Header variant="h2">{es.processing.progress.title}</Header>}>
      <SpaceBetween size="l">
        {error && <Alert type="error">{error}</Alert>}

        {!summary && !error && (
          <SpaceBetween size="s">
            <div style={{ transition: 'all 0.5s ease-in-out' }}>
              <ProgressBar
                value={percentage}
                label={`Procesando archivo ${currentIndex + 1} de ${totalFiles}`}
                description={`Archivo actual: ${currentFile}`}
                additionalInfo={`Tiempo transcurrido: ${elapsedDisplay}`}
                variant="standalone"
              />
            </div>
            <Box float="right">
              <Button
                variant="normal"
                onClick={handleCancel}
                loading={cancelling}
                disabled={cancelling}
                iconName="close"
              >
                Cancelar procesamiento
              </Button>
            </Box>
          </SpaceBetween>
        )}

        {summary && (
          <SpaceBetween size="m">
            <Alert type={summary.cancelled ? 'info' : summary.failed > 0 ? 'warning' : 'success'}>
              {summary.cancelled
                ? `Procesamiento cancelado. Se procesaron ${summary.success + summary.failed} de ${summary.total} archivos.`
                : summary.failed > 0
                  ? `Procesamiento completado con ${summary.failed} error(es).`
                  : 'Procesamiento completado exitosamente.'}
            </Alert>
            <Box variant="h3">Resumen</Box>
            <KeyValuePairs
              columns={3}
              items={[
                { label: 'Total archivos', value: String(summary.total) },
                { label: 'Exitosos', value: String(summary.success) },
                { label: 'Fallidos', value: String(summary.failed) },
                { label: 'Entidades detectadas', value: String(summary.totalEntities) },
                { label: 'Tiempo total', value: formatDuration(summary.elapsedMs) },
                { label: 'Volumen procesado', value: formatBytes(summary.totalVolumeBytes) },
              ]}
            />
          </SpaceBetween>
        )}
      </SpaceBetween>
    </Container>
  );
};

export default ProcessingProgress;
