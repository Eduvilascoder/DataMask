import React, { useState, useCallback, useEffect } from 'react';
import {
  Container,
  Header,
  SpaceBetween,
  Alert,
  Flashbar,
  StatusIndicator,
  Box,
} from '@cloudscape-design/components';
import type { FileInfo } from '../types';
import { validateFolder, startProcessing } from '../services/api';
import { useProcessing } from '../context/ProcessingContext';
import FolderInput from '../components/FolderInput';
import FileList from '../components/FileList';
import ProcessingProgress from '../components/ProcessingProgress';
import es from '../i18n/es';

interface EngineStatus {
  ollama: { available: boolean; model: string; url: string; reason?: string };
  spacy: { available: boolean; model: string };
  active_engine: string;
  configured_engine?: string;
}

const ProcessingPage: React.FC = () => {
  // Usar context para estado persistente (no se pierde al navegar)
  const { state, setFolderPath, setFiles, setIsProcessing } = useProcessing();

  const [isValidating, setIsValidating] = useState(false);
  const [validationError, setValidationError] = useState<string | undefined>();
  const [engineStatus, setEngineStatus] = useState<EngineStatus | null>(null);
  const [flashMessages, setFlashMessages] = useState<Array<{
    type: 'success' | 'error' | 'info';
    content: string;
    id: string;
    dismissible: boolean;
  }>>([]);

  useEffect(() => {
    const fetchEngineStatus = async () => {
      try {
        const response = await fetch('/api/status/engine');
        if (response.ok) {
          const data: EngineStatus = await response.json();
          setEngineStatus(data);
        }
      } catch {
        // Silently fail
      }
    };
    fetchEngineStatus();
  }, []);

  const handleValidate = async (path: string) => {
    setIsValidating(true);
    setValidationError(undefined);
    setFiles([]);
    setFolderPath('');

    try {
      const response = await validateFolder(path);
      if (response.valid) {
        setFiles(response.files);
        setFolderPath(path);
        if (response.files.length === 0) {
          setValidationError(es.processing.fileList.noFiles);
        }
      } else {
        setValidationError(response.error || es.errors.unknownError);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : es.errors.networkError;
      setValidationError(message);
    } finally {
      setIsValidating(false);
    }
  };

  const handleStartProcessing = async (selectedFiles?: FileInfo[]) => {
    if (!state.folderPath) return;

    setIsProcessing(true);
    setFlashMessages([]);

    try {
      const fileNames = selectedFiles && selectedFiles.length > 0
        ? selectedFiles.map(f => f.name)
        : undefined;
      await startProcessing(state.folderPath, fileNames);
    } catch (err) {
      const message = err instanceof Error ? err.message : es.errors.unknownError;
      setFlashMessages([{
        type: 'error',
        content: message,
        id: 'process-error',
        dismissible: true,
      }]);
      setIsProcessing(false);
    }
  };

  const handleProcessingComplete = useCallback(() => {
    setIsProcessing(false);
  }, [setIsProcessing]);

  const renderEngineStatus = () => {
    if (!engineStatus) return null;

    if (engineStatus.active_engine === 'ollama') {
      return (
        <Box margin={{ bottom: 's' }}>
          <StatusIndicator type="success">
            Ollama activo ({engineStatus.ollama?.model || 'modelo desconocido'})
          </StatusIndicator>
        </Box>
      );
    } else if (engineStatus.active_engine === 'spacy') {
      const isDisabledByConfig = engineStatus.configured_engine === 'spacy';
      const reason = engineStatus.ollama?.reason;
      return (
        <Box margin={{ bottom: 's' }}>
          <StatusIndicator type={isDisabledByConfig ? 'info' : 'warning'}>
            {isDisabledByConfig
              ? 'Ollama deshabilitado — usando spaCy (configurado por usuario)'
              : `spaCy activo — ${reason || 'Ollama no disponible'}`}
          </StatusIndicator>
        </Box>
      );
    } else {
      return (
        <Box margin={{ bottom: 's' }}>
          <StatusIndicator type="error">
            Sin motor NER
          </StatusIndicator>
        </Box>
      );
    }
  };

  return (
    <SpaceBetween size="l">
      {flashMessages.length > 0 && (
        <Flashbar
          items={flashMessages.map((msg) => ({
            ...msg,
            onDismiss: () =>
              setFlashMessages((prev) => prev.filter((m) => m.id !== msg.id)),
          }))}
        />
      )}

      {renderEngineStatus()}

      <Container
        header={
          <Header variant="h1" description={es.processing.description}>
            {es.processing.title}
          </Header>
        }
      >
        <SpaceBetween size="l">
          <FolderInput
            onValidate={handleValidate}
            isLoading={isValidating}
            errorText={validationError}
          />

          {state.files.length > 0 && (
            <FileList
              files={state.files}
              onStartProcessing={handleStartProcessing}
              isProcessing={state.isProcessing}
            />
          )}
        </SpaceBetween>
      </Container>

      <ProcessingProgress
        isActive={state.isProcessing}
        onComplete={handleProcessingComplete}
      />

      {!state.isProcessing && state.files.length === 0 && !validationError && (
        <Alert type="info">
          {es.processing.description}
        </Alert>
      )}
    </SpaceBetween>
  );
};

export default ProcessingPage;
