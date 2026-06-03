import React, { useEffect, useState, useCallback } from 'react';
import {
  Table,
  Header,
  Pagination,
  Box,
  Button,
  StatusIndicator,
  Badge,
  SpaceBetween,
  Modal,
} from '@cloudscape-design/components';
import type { AuditLogEntry } from '../types';
import { getLogs, deleteLogs } from '../services/api';
import es from '../i18n/es';

const PAGE_SIZE = 100;

/** Formatea bytes a una representación legible. */
function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} ${es.general.bytes}`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} ${es.general.kb}`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} ${es.general.mb}`;
}

/** Formatea un timestamp ISO 8601 a formato legible. */
function formatTimestamp(timestamp: string): string {
  try {
    const date = new Date(timestamp);
    return date.toLocaleString('es-AR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  } catch {
    return timestamp;
  }
}

/** Renderiza un badge para el motor NER utilizado. */
function renderEngineBadge(engine: string | null): React.ReactNode {
  if (!engine) return <Badge color="grey">—</Badge>;
  if (engine === 'ollama') return <Badge color="green">Ollama</Badge>;
  if (engine === 'spacy') return <Badge color="blue">spaCy</Badge>;
  return <Badge color="grey">{engine}</Badge>;
}

const LogTable: React.FC = () => {
  const [entries, setEntries] = useState<AuditLogEntry[]>([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const fetchLogs = useCallback(async (page: number) => {
    setLoading(true);
    setError(null);
    try {
      const response = await getLogs(page, PAGE_SIZE);
      setEntries(response.entries);
      setTotalPages(Math.max(1, Math.ceil(response.total / PAGE_SIZE)));
    } catch (err) {
      setError(err instanceof Error ? err.message : es.errors.unknownError);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchLogs(currentPage);
  }, [currentPage, fetchLogs]);

  const handleDeleteLogs = async () => {
    setDeleting(true);
    try {
      await deleteLogs();
      setShowDeleteModal(false);
      setCurrentPage(1);
      await fetchLogs(1);
    } catch (err) {
      setError(err instanceof Error ? err.message : es.errors.unknownError);
    } finally {
      setDeleting(false);
    }
  };

  return (
    <>
      <Table
        header={
          <Header
            actions={
              <SpaceBetween direction="horizontal" size="xs">
                <Button
                  iconName="remove"
                  onClick={() => setShowDeleteModal(true)}
                  disabled={entries.length === 0}
                >
                  Borrar registros
                </Button>
                <Button iconName="refresh" onClick={() => fetchLogs(currentPage)}>
                  {es.logs.refresh}
                </Button>
              </SpaceBetween>
            }
          >
            {es.logs.title}
          </Header>
        }
        columnDefinitions={[
          {
            id: 'filename',
            header: es.logs.columns.filename,
            cell: (item: AuditLogEntry) => item.filename,
            sortingField: 'filename',
          },
          {
            id: 'size',
            header: es.logs.columns.size,
            cell: (item: AuditLogEntry) => formatFileSize(item.file_size_bytes),
          },
          {
            id: 'user',
            header: es.logs.columns.user,
            cell: (item: AuditLogEntry) => item.os_user,
          },
          {
            id: 'timestamp',
            header: es.logs.columns.timestamp,
            cell: (item: AuditLogEntry) => formatTimestamp(item.timestamp),
            sortingField: 'timestamp',
          },
          {
            id: 'engine',
            header: 'Motor',
            cell: (item: AuditLogEntry) => renderEngineBadge(item.engine),
          },
          {
            id: 'processing_time',
            header: 'Tiempo',
            cell: (item: AuditLogEntry) => {
              const ms = item.processing_time_ms || 0;
              if (ms < 1000) return `${ms} ms`;
              const s = (ms / 1000).toFixed(1);
              return `${s}s`;
            },
          },
          {
            id: 'result',
            header: es.logs.columns.result,
            cell: (item: AuditLogEntry) => (
              <StatusIndicator type={item.result === 'success' ? 'success' : 'error'}>
                {item.result === 'success' ? es.logs.results.success : es.logs.results.error}
              </StatusIndicator>
            ),
          },
          {
            id: 'entities',
            header: es.logs.columns.entities,
            cell: (item: AuditLogEntry) => String(item.entities_detected),
          },
        ]}
        items={entries}
        loading={loading}
        loadingText={es.general.loading}
        empty={
          <Box textAlign="center" color="text-body-secondary" padding="l">
            {error || es.logs.noLogs}
          </Box>
        }
        pagination={
          <Pagination
            currentPageIndex={currentPage}
            pagesCount={totalPages}
            onChange={({ detail }) => setCurrentPage(detail.currentPageIndex)}
          />
        }
        variant="full-page"
        stripedRows
      />
      <Modal
        visible={showDeleteModal}
        onDismiss={() => setShowDeleteModal(false)}
        header="Confirmar eliminación"
        footer={
          <Box float="right">
            <SpaceBetween direction="horizontal" size="xs">
              <Button variant="link" onClick={() => setShowDeleteModal(false)}>
                Cancelar
              </Button>
              <Button variant="primary" onClick={handleDeleteLogs} loading={deleting}>
                Eliminar
              </Button>
            </SpaceBetween>
          </Box>
        }
      >
        ¿Está seguro de que desea eliminar todos los registros de auditoría? Esta acción no se puede deshacer.
      </Modal>
    </>
  );
};

export default LogTable;
