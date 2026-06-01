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
import FolderInput from '../components/FolderInput';
import FileList from '../components/FileList';
import ProcessingProgress from '../components/ProcessingProgress';
import es from '../i18n/es';

interface EngineStatus {
  ollama: { available: boolean; model: string; url: string };
  spacy: { available: boolean; model: string };
  active_engine: string;
}

const ProcessingPage: React.FC = () => {
  const [files, setFiles] = useState<FileInfo[]>([]);
  const [folderPath, setFolderPath] = useState('');
  const [isValidating, setIsValidating] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
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
        // Silently fail — status indicator just won't show
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
    if (!folderPath) return;

    setIsProcessing(true);
    setFlashMessages([]);

    try {
      const fileNames = selectedFiles && selectedFiles.length > 0
        ? selectedFiles.map(f => f.name)
        : undefined;
      await startProcessing(folderPath, fileNames);
    } catch (err) {
      const message = err instanceof Error ? err.message : es.errors.unknownError;
      setFlashMessages([
        {
          type: 'error',
          content: message,
          id: 'process-error',
          dismissible: true,
        },
      ]);
      setIsProcessing(false);
    }
  };

  const handleProcessingComplete = useCallback(() => {
    setIsProcessing(false);
  }, []);

  const renderEngineStatus = () => {
    if (!engineStatus) return null;

    if (engineStatus.active_engine === 'ollama') {
      return (
        <Box margin={{ bottom: 's' }}>
          <StatusIndicator type="success">
            Ollama activo (Llama 3.1 8B)
          </StatusIndicator>
        </Box>
      );
    } else if (engineStatus.active_engine === 'spacy') {
      const isDisabledByConfig = (engineStatus as any).configured_engine === 'spacy';
      return (
        <Box margin={{ bottom: 's' }}>
          <StatusIndicator type={isDisabledByConfig ? 'info' : 'warning'}>
            {isDisabledByConfig
              ? 'Ollama deshabilitado — usando spaCy (configurado por usuario)'
              : 'spaCy activo (Ollama no disponible)'}
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

          {files.length > 0 && (
            <FileList
              files={files}
              onStartProcessing={handleStartProcessing}
              isProcessing={isProcessing}
            />
          )}
        </SpaceBetween>
      </Container>

      <ProcessingProgress
        isActive={isProcessing}
        onComplete={handleProcessingComplete}
      />

      {!isProcessing && files.length === 0 && !validationError && (
        <Alert type="info">
          {es.processing.description}
        </Alert>
      )}
    </SpaceBetween>
  );
};

export default ProcessingPage;
