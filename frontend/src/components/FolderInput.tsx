import React, { useState } from 'react';
import {
  SpaceBetween,
  Input,
  Button,
  FormField,
  Modal,
  Box,
  Table,
  Icon,
  Header,
} from '@cloudscape-design/components';
import { browseFolders, type DirectoryEntry, type BrowseResponse } from '../services/api';
import es from '../i18n/es';

interface FolderInputProps {
  onValidate: (path: string) => void;
  isLoading: boolean;
  errorText?: string;
}

const FolderInput: React.FC<FolderInputProps> = ({ onValidate, isLoading, errorText }) => {
  const [path, setPath] = useState('');
  const [showBrowser, setShowBrowser] = useState(false);
  const [browseData, setBrowseData] = useState<BrowseResponse | null>(null);
  const [browseLoading, setBrowseLoading] = useState(false);

  const handleValidate = (folderPath: string) => {
    if (folderPath.trim()) {
      onValidate(folderPath.trim());
    }
  };

  const handleKeyDown = (event: CustomEvent<{ key: string }>) => {
    if (event.detail.key === 'Enter' && path.trim()) {
      handleValidate(path);
    }
  };

  const openBrowser = async () => {
    setShowBrowser(true);
    setBrowseLoading(true);
    try {
      const data = await browseFolders(path || undefined);
      setBrowseData(data);
    } catch {
      const data = await browseFolders();
      setBrowseData(data);
    } finally {
      setBrowseLoading(false);
    }
  };

  const navigateTo = async (targetPath: string) => {
    setBrowseLoading(true);
    try {
      const data = await browseFolders(targetPath);
      setBrowseData(data);
    } catch {
      // Stay on current path
    } finally {
      setBrowseLoading(false);
    }
  };

  const selectFolder = () => {
    if (browseData) {
      const selectedPath = browseData.current_path;
      setPath(selectedPath);
      setShowBrowser(false);
      // Validar automáticamente al seleccionar
      handleValidate(selectedPath);
    }
  };

  return (
    <>
      <SpaceBetween size="s" direction="horizontal">
        <FormField
          label={es.processing.folderInput.label}
          errorText={errorText}
          description="Explore y seleccione una carpeta con el botón, o ingrese la ruta manualmente y presione Enter"
          stretch
        >
          <Input
            value={path}
            onChange={({ detail }) => setPath(detail.value)}
            onKeyDown={handleKeyDown}
            placeholder="La ruta aparecerá aquí al seleccionar una carpeta..."
            type="text"
          />
        </FormField>
        <FormField label="&nbsp;">
          <Button
            variant="primary"
            iconName="folder-open"
            onClick={openBrowser}
            disabled={isLoading}
            loading={isLoading}
          >
            {isLoading ? 'Cargando...' : 'Explorar carpetas'}
          </Button>
        </FormField>
      </SpaceBetween>

      <Modal
        visible={showBrowser}
        onDismiss={() => setShowBrowser(false)}
        header={
          <Header description={browseData?.current_path || ''}>
            Seleccionar carpeta
          </Header>
        }
        size="large"
        footer={
          <Box float="right">
            <SpaceBetween size="xs" direction="horizontal">
              <Button onClick={() => setShowBrowser(false)}>
                Cancelar
              </Button>
              <Button variant="primary" onClick={selectFolder}>
                Seleccionar esta carpeta
              </Button>
            </SpaceBetween>
          </Box>
        }
      >
        <SpaceBetween size="s">
          {browseData?.parent_path && (
            <Button
              iconName="arrow-left"
              onClick={() => navigateTo(browseData.parent_path!)}
              disabled={browseLoading}
            >
              Subir un nivel
            </Button>
          )}
          <Table
            loading={browseLoading}
            loadingText="Cargando..."
            items={browseData?.entries || []}
            empty={
              <Box textAlign="center" color="inherit">
                <b>Carpeta vacía</b>
                <Box padding={{ bottom: 's' }} variant="p" color="inherit">
                  No se encontraron carpetas ni documentos.
                </Box>
              </Box>
            }
            columnDefinitions={[
              {
                id: 'icon',
                header: '',
                width: 40,
                cell: (item: DirectoryEntry) => (
                  <Icon name={item.is_dir ? 'folder' : 'file'} />
                ),
              },
              {
                id: 'name',
                header: 'Nombre',
                cell: (item: DirectoryEntry) =>
                  item.is_dir ? (
                    <Button
                      variant="link"
                      onClick={() => navigateTo(item.path)}
                    >
                      {item.name}
                    </Button>
                  ) : (
                    <span>{item.name}</span>
                  ),
              },
              {
                id: 'type',
                header: 'Tipo',
                width: 150,
                cell: (item: DirectoryEntry) =>
                  item.is_dir ? 'Carpeta' : item.name.split('.').pop()?.toUpperCase() || 'Archivo',
              },
            ]}
          />
        </SpaceBetween>
      </Modal>
    </>
  );
};

export default FolderInput;
