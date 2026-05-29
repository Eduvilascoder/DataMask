import React, { useEffect, useState, useRef } from 'react';
import {
  ProgressBar,
  Container,
  Header,
  SpaceBetween,
  Box,
  Alert,
  KeyValuePairs,
} from '@cloudscape-design/components';
import { connectToProgress } from '../services/sse';
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
}

const ProcessingProgress: React.FC<ProcessingProgressProps> = ({ isActive, onComplete }) => {
  const [percentage, setPercentage] = useState(0);
  const [currentFile, setCurrentFile] = useState('');
  const [currentIndex, setCurrentIndex] = useState(0);
  const [totalFiles, setTotalFiles] = useState(0);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const disconnectRef = useRef<(() => void) | null>(null);

  useEffect(() => {
    if (!isActive) return;

    setPercentage(0);
    setCurrentFile('');
    setSummary(null);
    setError(null);
    setCurrentIndex(0);
    setTotalFiles(0);

    const disconnect = connectToProgress(
      (event: any) => {
        const type = event.type;

        if (type === 'file_start') {
          setCurrentFile(event.file || '');
          setCurrentIndex(event.index || 0);
          setTotalFiles(event.total || 0);
          const pct = event.total > 0 ? Math.round((event.index / event.total) * 100) : 0;
          setPercentage(pct);
        }

        if (type === 'file_complete') {
          const pct = event.total > 0 ? Math.round(((event.index + 1) / event.total) * 100) : 100;
          setPercentage(pct);
        }

        if (type === 'file_error') {
          // Continue — just update progress
          const pct = event.total > 0 ? Math.round(((event.index + 1) / event.total) * 100) : 100;
          setPercentage(pct);
        }

        if (type === 'complete') {
          setPercentage(100);
          const results = event.results || [];
          const totalEntities = results.reduce(
            (sum: number, r: any) => sum + (r.entities_found || 0), 0
          );
          setSummary({
            total: event.total || 0,
            success: event.success || 0,
            failed: event.failed || 0,
            totalEntities,
          });
          onComplete();
        }

        if (type === 'error') {
          setError(event.message || 'Error desconocido durante el procesamiento.');
          onComplete();
        }
      },
      (errorMsg: string) => {
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
  }, [isActive, onComplete]);

  if (!isActive && !summary && !error) return null;

  return (
    <Container header={<Header variant="h2">{es.processing.progress.title}</Header>}>
      <SpaceBetween size="l">
        {error && <Alert type="error">{error}</Alert>}

        {!summary && !error && (
          <SpaceBetween size="s">
            <ProgressBar
              value={percentage}
              label={`Procesando archivo ${currentIndex + 1} de ${totalFiles}`}
              description={`Archivo actual: ${currentFile}`}
              variant="standalone"
            />
          </SpaceBetween>
        )}

        {summary && (
          <SpaceBetween size="m">
            <Alert type={summary.failed > 0 ? 'warning' : 'success'}>
              {summary.failed > 0
                ? `Procesamiento completado con ${summary.failed} error(es).`
                : 'Procesamiento completado exitosamente.'}
            </Alert>
            <Box variant="h3">Resumen</Box>
            <KeyValuePairs
              columns={4}
              items={[
                { label: 'Total archivos', value: String(summary.total) },
                { label: 'Exitosos', value: String(summary.success) },
                { label: 'Fallidos', value: String(summary.failed) },
                { label: 'Entidades detectadas', value: String(summary.totalEntities) },
              ]}
            />
          </SpaceBetween>
        )}
      </SpaceBetween>
    </Container>
  );
};

export default ProcessingProgress;
