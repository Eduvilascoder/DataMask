import React, { useEffect, useState } from 'react';
import {
  Container,
  Header,
  SpaceBetween,
  Table,
  Button,
  Box,
  Flashbar,
  Tabs,
  Icon,
} from '@cloudscape-design/components';

interface OutputFile {
  name: string;
  size_bytes: number;
  path: string;
  folder: string;
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

const OutputPage: React.FC = () => {
  const [pdfFiles, setPdfFiles] = useState<OutputFile[]>([]);
  const [mdFiles, setMdFiles] = useState<OutputFile[]>([]);
  const [selectedPdf, setSelectedPdf] = useState<OutputFile[]>([]);
  const [selectedMd, setSelectedMd] = useState<OutputFile[]>([]);
  const [loading, setLoading] = useState(true);
  const [flashMessages, setFlashMessages] = useState<Array<{
    type: 'success' | 'error';
    content: string;
    id: string;
    dismissible: boolean;
  }>>([]);

  const fetchFiles = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/output/files?folder=all');
      const data = await response.json();
      setPdfFiles(data.files.filter((f: OutputFile) => f.folder === 'ofuscados'));
      setMdFiles(data.files.filter((f: OutputFile) => f.folder === 'ofuscados_md'));
    } catch {
      setFlashMessages([{
        type: 'error',
        content: 'Error al cargar archivos.',
        id: 'load-err',
        dismissible: true,
      }]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchFiles(); }, []);

  const handleDelete = async (files: OutputFile[], folder: string) => {
    try {
      const response = await fetch('/api/output/delete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ files: files.map(f => f.name), folder }),
      });
      const data = await response.json();
      setFlashMessages([{
        type: 'success',
        content: `${data.deleted} archivo(s) eliminado(s).`,
        id: `del-${Date.now()}`,
        dismissible: true,
      }]);
      setSelectedPdf([]);
      setSelectedMd([]);
      fetchFiles();
    } catch {
      setFlashMessages([{
        type: 'error',
        content: 'Error al eliminar archivos.',
        id: `del-err-${Date.now()}`,
        dismissible: true,
      }]);
    }
  };

  const handleDeleteAll = async (folder: string) => {
    try {
      const response = await fetch(`/api/output/delete-all?folder=${folder}`, { method: 'POST' });
      const data = await response.json();
      setFlashMessages([{
        type: 'success',
        content: `${data.deleted} archivo(s) eliminado(s).`,
        id: `delall-${Date.now()}`,
        dismissible: true,
      }]);
      setSelectedPdf([]);
      setSelectedMd([]);
      fetchFiles();
    } catch {
      setFlashMessages([{
        type: 'error',
        content: 'Error al eliminar archivos.',
        id: `delall-err-${Date.now()}`,
        dismissible: true,
      }]);
    }
  };

  const renderTable = (
    files: OutputFile[],
    selected: OutputFile[],
    setSelected: (items: OutputFile[]) => void,
    folder: string,
  ) => (
    <Table
      loading={loading}
      loadingText="Cargando..."
      selectionType="multi"
      selectedItems={selected}
      onSelectionChange={({ detail }) => setSelected(detail.selectedItems as OutputFile[])}
      trackBy="name"
      empty={
        <Box textAlign="center" color="inherit" padding="l">
          <b>Sin archivos</b>
          <Box variant="p" color="inherit">
            No hay archivos ofuscados en esta carpeta.
          </Box>
        </Box>
      }
      header={
        <Header
          counter={`(${files.length})`}
          actions={
            <SpaceBetween size="xs" direction="horizontal">
              <Button
                disabled={selected.length === 0}
                onClick={() => handleDelete(selected, folder)}
              >
                Eliminar seleccionados ({selected.length})
              </Button>
              <Button
                disabled={files.length === 0}
                onClick={() => handleDeleteAll(folder)}
              >
                Eliminar todos
              </Button>
              <Button iconName="refresh" onClick={fetchFiles}>
                Actualizar
              </Button>
            </SpaceBetween>
          }
        >
          Archivos
        </Header>
      }
      columnDefinitions={[
        {
          id: 'icon',
          header: '',
          width: 40,
          cell: (item: OutputFile) => (
            <Icon name={item.name.endsWith('.md') ? 'file' : 'file'} />
          ),
        },
        {
          id: 'name',
          header: 'Nombre',
          cell: (item: OutputFile) => (
            <Button
              variant="link"
              onClick={() => {
                const url = `/api/output/view/${item.folder}/${item.name}`;
                window.open(url, '_blank');
              }}
            >
              {item.name}
            </Button>
          ),
          sortingField: 'name',
        },
        {
          id: 'size',
          header: 'Tamaño',
          width: 120,
          cell: (item: OutputFile) => formatFileSize(item.size_bytes),
        },
        {
          id: 'actions',
          header: 'Acciones',
          width: 100,
          cell: (item: OutputFile) => (
            <Button
              variant="icon"
              iconName="external"
              onClick={() => {
                const url = `/api/output/view/${item.folder}/${item.name}`;
                window.open(url, '_blank');
              }}
            />
          ),
        },
      ]}
      items={files}
      stripedRows
    />
  );

  return (
    <SpaceBetween size="l">
      {flashMessages.length > 0 && (
        <Flashbar items={flashMessages.map(msg => ({
          ...msg,
          onDismiss: () => setFlashMessages(prev => prev.filter(m => m.id !== msg.id)),
        }))} />
      )}

      <Container
        header={
          <Header
            variant="h1"
            description="Explore y gestione los archivos ofuscados generados (PDF y Markdown)."
          >
            Archivos ofuscados
          </Header>
        }
      >
        <Tabs
          tabs={[
            {
              id: 'pdf',
              label: `PDF y Word ofuscados (${pdfFiles.length})`,
              content: renderTable(pdfFiles, selectedPdf, setSelectedPdf, 'ofuscados'),
            },
            {
              id: 'md',
              label: `Markdown ofuscados (${mdFiles.length})`,
              content: renderTable(mdFiles, selectedMd, setSelectedMd, 'ofuscados_md'),
            },
          ]}
        />
      </Container>
    </SpaceBetween>
  );
};

export default OutputPage;
