import type { FolderValidationResponse, TypeConfig, LogsResponse } from '../types';

const BASE_URL = '/api';

/** Maneja errores de respuesta HTTP. */
async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    const message = errorData?.detail || `Error HTTP ${response.status}`;
    throw new Error(message);
  }
  return response.json() as Promise<T>;
}

/** Valida una ruta de carpeta y retorna la lista de PDFs encontrados. */
export async function validateFolder(path: string): Promise<FolderValidationResponse> {
  const response = await fetch(`${BASE_URL}/folders/validate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path }),
  });
  return handleResponse<FolderValidationResponse>(response);
}

/** Obtiene la configuración actual de tipos de datos sensibles. */
export async function getConfig(): Promise<TypeConfig> {
  const response = await fetch(`${BASE_URL}/config`);
  return handleResponse<TypeConfig>(response);
}

/** Actualiza la configuración de tipos de datos sensibles. */
export async function updateConfig(config: TypeConfig): Promise<TypeConfig> {
  const response = await fetch(`${BASE_URL}/config`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config),
  });
  return handleResponse<TypeConfig>(response);
}

/** Inicia el procesamiento de PDFs en la carpeta indicada. */
export async function startProcessing(folderPath: string, selectedFiles?: string[]): Promise<{ message: string }> {
  const body: Record<string, any> = { folder_path: folderPath };
  if (selectedFiles && selectedFiles.length > 0) {
    body.selected_files = selectedFiles;
  }
  const response = await fetch(`${BASE_URL}/process`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  return handleResponse<{ message: string }>(response);
}

/** Obtiene los registros de auditoría paginados. */
export async function getLogs(page: number = 1, pageSize: number = 100): Promise<LogsResponse> {
  const response = await fetch(`${BASE_URL}/logs?page=${page}&page_size=${pageSize}`);
  return handleResponse<LogsResponse>(response);
}

/** Navega directorios del sistema de archivos local. */
export interface DirectoryEntry {
  name: string;
  path: string;
  is_dir: boolean;
}

export interface BrowseResponse {
  current_path: string;
  parent_path: string | null;
  entries: DirectoryEntry[];
}

export async function browseFolders(path?: string): Promise<BrowseResponse> {
  const response = await fetch(`${BASE_URL}/folders/browse`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path: path || null }),
  });
  return handleResponse<BrowseResponse>(response);
}
