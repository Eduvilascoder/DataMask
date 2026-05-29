import React, { useState, useCallback } from 'react';
import {
  Container,
  Header,
  SpaceBetween,
  Alert,
  Flashbar,
} from '@cloudscape-design/components';
import type { FileInfo } from '../types';
import { validateFolder, startProcessing } from '../services/api';
import FolderInput from '../components/FolderInput';
import FileList from '../components/FileList';
import ProcessingProgress from '../components/ProcessingProgress';
import es from '../i18n/es';

const ProcessingPage: React.FC = () => {
  const [files, setFiles] = useState<FileInfo[]>([]);
  const [folderPath, setFolderPath] = useState('');
  const [isValidating, setIsValidating] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [validationError, setValidationError] = useState<string | undefined>();
  const [flashMessages, setFlashMessages] = useState<Array<{
    type: 'success' | 'error' | 'info';
    content: string;
    id: string;
    dismissible: boolean;
  }>>([]);

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
