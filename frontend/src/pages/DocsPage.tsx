import React, { useEffect, useState } from 'react';
import {
  Container,
  Header,
  SpaceBetween,
  Table,
  Button,
  Box,
  Modal,
} from '@cloudscape-design/components';

interface DocFile {
  name: string;
  title: string;
  size_bytes: number;
}

const DocsPage: React.FC = () => {
  const [docs, setDocs] = useState<DocFile[]>([]);
  const [loading, setLoading] = useState(true);
  const [viewContent, setViewContent] = useState<string | null>(null);
  const [viewTitle, setViewTitle] = useState('');

  useEffect(() => {
    const fetchDocs = async () => {
      try {
        const response = await fetch('/api/docs/list');
        const data = await response.json();
        setDocs(data.files || []);
      } catch {
        // ignore
      } finally {
        setLoading(false);
      }
    };
    fetchDocs();
  }, []);

  const handleView = async (doc: DocFile) => {
    try {
      const response = await fetch(`/api/docs/view/${doc.name}`);
      const data = await response.json();
      setViewContent(data.content);
      setViewTitle(doc.title);
    } catch {
      setViewContent('Error al cargar el documento.');
      setViewTitle(doc.title);
    }
  };

  return (
    <SpaceBetween size="l">
      <Container
        header={
          <Header
            variant="h1"
            description="Documentación técnica y guías del proyecto DataMask."
          >
            Documentación
          </Header>
        }
      >
        <Table
          loading={loading}
          loadingText="Cargando documentos..."
          items={docs}
          empty={
            <Box textAlign="center" padding="l">
              <b>Sin documentación</b>
              <Box variant="p">No se encontraron archivos de documentación.</Box>
            </Box>
          }
          columnDefinitions={[
            {
              id: 'title',
              header: 'Documento',
              cell: (item: DocFile) => (
                <Button variant="link" onClick={() => handleView(item)}>
                  {item.title}
                </Button>
              ),
            },
            {
              id: 'name',
              header: 'Archivo',
              cell: (item: DocFile) => <code>{item.name}</code>,
              width: 220,
            },
            {
              id: 'actions',
              header: 'Acciones',
              width: 100,
              cell: (item: DocFile) => (
                <Button
                  variant="icon"
                  iconName="external"
                  onClick={() => handleView(item)}
                />
              ),
            },
          ]}
          stripedRows
        />
      </Container>

      <Modal
        visible={viewContent !== null}
        onDismiss={() => setViewContent(null)}
        header={viewTitle}
        size="max"
        footer={
          <Box float="right">
            <Button onClick={() => setViewContent(null)}>Cerrar</Button>
          </Box>
        }
      >
        <Box padding="s">
          <pre style={{
            whiteSpace: 'pre-wrap',
            wordWrap: 'break-word',
            fontFamily: 'monospace',
            fontSize: '13px',
            lineHeight: '1.5',
            maxHeight: '70vh',
            overflow: 'auto',
          }}>
            {viewContent}
          </pre>
        </Box>
      </Modal>
    </SpaceBetween>
  );
};

export default DocsPage;
