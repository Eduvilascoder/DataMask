import React, { createContext, useContext, useState, useCallback } from 'react';
import type { FileInfo } from '../types';

interface ProcessingState {
  folderPath: string;
  files: FileInfo[];
  selectedFiles: FileInfo[];
  isProcessing: boolean;
  startTime: number | null;
  elapsedMs: number | null;
}

interface ProcessingContextType {
  state: ProcessingState;
  setFolderPath: (path: string) => void;
  setFiles: (files: FileInfo[]) => void;
  setSelectedFiles: (files: FileInfo[]) => void;
  setIsProcessing: (processing: boolean) => void;
  startTimer: () => void;
  stopTimer: () => void;
  getElapsedMs: () => number;
}

const initialState: ProcessingState = {
  folderPath: '',
  files: [],
  selectedFiles: [],
  isProcessing: false,
  startTime: null,
  elapsedMs: null,
};

const ProcessingContext = createContext<ProcessingContextType | null>(null);

export const ProcessingProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, setState] = useState<ProcessingState>(initialState);

  const setFolderPath = useCallback((path: string) => {
    setState(prev => ({ ...prev, folderPath: path }));
  }, []);

  const setFiles = useCallback((files: FileInfo[]) => {
    setState(prev => ({ ...prev, files }));
  }, []);

  const setSelectedFiles = useCallback((files: FileInfo[]) => {
    setState(prev => ({ ...prev, selectedFiles: files }));
  }, []);

  const setIsProcessing = useCallback((isProcessing: boolean) => {
    setState(prev => ({ ...prev, isProcessing }));
  }, []);

  const startTimer = useCallback(() => {
    setState(prev => ({ ...prev, startTime: Date.now(), elapsedMs: null }));
  }, []);

  const stopTimer = useCallback(() => {
    setState(prev => {
      const elapsed = prev.startTime ? Date.now() - prev.startTime : null;
      return { ...prev, elapsedMs: elapsed, startTime: null };
    });
  }, []);

  const getElapsedMs = useCallback((): number => {
    if (state.startTime) return Date.now() - state.startTime;
    return state.elapsedMs || 0;
  }, [state.startTime, state.elapsedMs]);

  return (
    <ProcessingContext.Provider value={{
      state,
      setFolderPath,
      setFiles,
      setSelectedFiles,
      setIsProcessing,
      startTimer,
      stopTimer,
      getElapsedMs,
    }}>
      {children}
    </ProcessingContext.Provider>
  );
};

export const useProcessing = (): ProcessingContextType => {
  const context = useContext(ProcessingContext);
  if (!context) throw new Error('useProcessing must be used within ProcessingProvider');
  return context;
};
