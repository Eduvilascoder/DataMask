import React from 'react';
import {
  Table,
  Header,
  Button,
  Box,
  SpaceBetween,
} from '@cloudscape-design/components';
import type { FileInfo } from '../types';
import { useProcessing } from '../context/ProcessingContext';
import es from '../i18n/es';

interface FileListProps {
  files: FileInfo[];
  onStartProcessing: (selectedFiles: FileInfo[]) => void;
  isProcessing: boolean;
}

/** Formatea bytes a una representación legible. */
function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} ${es.general.bytes}`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} ${es.general.kb}`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} ${es.general.mb}`;
}

const FileList: React.FC<FileListProps> = ({ files, onStartProcessing, isProcessing }) => {
  const { state, setSelectedFiles } = useProcessing();
  const selectedItems = state.selectedFiles;

  if (files.length === 0) {
    return (
      <Box textAlign="center" color="text-body-secondary" padding="l">
        {es.processing.fileList.noFiles}
      </Box>
    );
  }

  const allSelected = selectedItems.length === files.length;

  const handleSelectAll = () => {
    if (allSelected) {
      setSelectedFiles([]);
    } else {
      setSelectedFiles([...files]);
    }
  };

  return (
    <Table
      header={
        <Header
          counter={`(${selectedItems.length}/${files.length} seleccionados)`}
          actions={
            <SpaceBetween size="xs" direction="horizontal">
              <Button
                onClick={handleSelectAll}
                disabled={isProcessing}
              >
                {allSelected ? 'Deseleccionar todo' : 'Seleccionar todo'}
              </Button>
              <Button
                variant="primary"
                onClick={() => onStartProcessing(selectedItems.length > 0 ? selectedItems : files)}
                loading={isProcessing}
                disabled={isProcessing}
              >
                {es.processing.fileList.startProcessing}
                {selectedItems.length > 0 && selectedItems.length < files.length
                  ? ` (${selectedItems.length})`
                  : ''}
              </Button>
            </SpaceBetween>
          }
        >
          {es.processing.fileList.title}
        </Header>
      }
      selectionType="multi"
      selectedItems={selectedItems}
      onSelectionChange={({ detail }) => setSelectedFiles(detail.selectedItems as FileInfo[])}
      columnDefinitions={[
        {
          id: 'name',
          header: es.processing.fileList.columnName,
          cell: (item: FileInfo) => item.name,
          sortingField: 'name',
        },
        {
          id: 'size',
          header: es.processing.fileList.columnSize,
          cell: (item: FileInfo) => formatFileSize(item.size_bytes),
          sortingField: 'size_bytes',
        },
      ]}
      items={files}
      variant="embedded"
      stripedRows
      trackBy="path"
    />
  );
};

export default FileList;
