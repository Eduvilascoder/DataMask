import React, { createContext, useContext, useState, useCallback } from 'react';
import type { FileInfo } from '../types';

interface ProcessingState {
  folderPath: string;
  files: FileInfo[];
  isProcessing: boolean;
}

interface ProcessingContextType {
  state: ProcessingState;
  setFolderPath: (path: string) => void;
  setFiles: (files: FileInfo[]) => void;
  setIsProcessing: (processing: boolean) => void;
}

const initialState: ProcessingState = {
  folderPath: '',
  files: [],
  isProcessing: false,
};

const ProcessingContext = createContext<ProcessingContextType | null>(null);

export const ProcessingProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, setState] = useState<ProcessingState>(initialState);
  const setFolderPath = useCallback((path: string) => { setState(prev => ({ ...prev, folderPath: path })); }, []);
  const setFiles = useCallback((files: FileInfo[]) => { setState(prev => ({ ...prev, files })); }, []);
  const setIsProcessing = useCallback((isProcessing: boolean) => { setState(prev => ({ ...prev, isProcessing })); }, []);
  return (
    <ProcessingContext.Provider value={{ state, setFolderPath, setFiles, setIsProcessing }}>
      {children}
    </ProcessingContext.Provider>
  );
};

export const useProcessing = (): ProcessingContextType => {
  const context = useContext(ProcessingContext);
  if (!context) throw new Error('useProcessing must be used within ProcessingProvider');
  return context;
};
