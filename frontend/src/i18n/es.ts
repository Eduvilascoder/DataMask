/** Traducciones en español para toda la interfaz de usuario. */
const es = {
  // Navegación
  nav: {
    processing: 'Procesamiento',
    config: 'Configuración',
    logs: 'Registros de Auditoría',
    appName: 'DataMask',
  },

  // Página de procesamiento
  processing: {
    title: 'Procesamiento de Documentos',
    description: 'Seleccione una carpeta con archivos PDF, Markdown o Word para detectar y ofuscar datos sensibles.',
    folderInput: {
      label: 'Ruta de la carpeta',
      placeholder: 'Ingrese la ruta completa de la carpeta con documentos (PDF, Markdown, Word)',
      validateButton: 'Validar carpeta',
      validating: 'Validando...',
    },
    fileList: {
      title: 'Documentos encontrados',
      noFiles: 'No se encontraron documentos (PDF, Markdown o Word) en la carpeta indicada.',
      columnName: 'Nombre del archivo',
      columnSize: 'Tamaño',
      startProcessing: 'Iniciar procesamiento',
    },
    progress: {
      title: 'Progreso del procesamiento',
      processing: 'Procesando',
      of: 'de',
      files: 'archivos',
      currentFile: 'Archivo actual',
      complete: 'Procesamiento completado',
      summary: 'Resumen',
      totalFiles: 'Total de archivos',
      successful: 'Exitosos',
      failed: 'Fallidos',
      totalEntities: 'Entidades detectadas',
    },
  },

  // Página de configuración
  config: {
    title: 'Configuración de Tipos de Datos Sensibles',
    description: 'Active o desactive los tipos de datos sensibles que desea detectar y ofuscar.',
    saveButton: 'Guardar configuración',
    saving: 'Guardando...',
    saved: 'Configuración guardada correctamente.',
    error: 'Error al guardar la configuración.',
    minOneType: 'Debe mantener al menos un tipo de dato activo.',
    types: {
      nombre: 'Nombre y Apellido',
      email: 'Correo Electrónico',
      celular: 'Celular',
      telefono: 'Teléfono',
      direccion: 'Dirección',
      tarjeta_credito: 'Tarjeta de Crédito',
      cuenta_bancaria: 'Cuenta Bancaria',
      dni: 'DNI',
      cuit_cuil: 'CUIT/CUIL',
      pasaporte: 'Pasaporte',
    },
    descriptions: {
      nombre: 'Detecta nombres y apellidos de personas',
      email: 'Detecta direcciones de correo electrónico',
      celular: 'Detecta números de celular con prefijo +54 9',
      telefono: 'Detecta números de teléfono fijo con prefijo +54',
      direccion: 'Detecta direcciones postales',
      tarjeta_credito: 'Detecta números de tarjeta de crédito (16 dígitos)',
      cuenta_bancaria: 'Detecta números de cuenta bancaria',
      dni: 'Detecta DNI en formato XX.XXX.XXX o XXXXXXXX',
      cuit_cuil: 'Detecta CUIT/CUIL en formato XX-XXXXXXXX-X',
      pasaporte: 'Detecta números de pasaporte argentino',
    },
  },

  // Página de logs
  logs: {
    title: 'Registros de Auditoría',
    description: 'Historial de archivos procesados con detalle de resultados.',
    noLogs: 'No hay registros de auditoría disponibles.',
    columns: {
      filename: 'Archivo',
      size: 'Tamaño',
      user: 'Usuario',
      timestamp: 'Fecha y Hora',
      result: 'Resultado',
      entities: 'Entidades',
    },
    results: {
      success: 'Éxito',
      error: 'Error',
    },
    refresh: 'Actualizar',
  },

  // Mensajes generales
  general: {
    loading: 'Cargando...',
    error: 'Error',
    success: 'Éxito',
    cancel: 'Cancelar',
    close: 'Cerrar',
    bytes: 'bytes',
    kb: 'KB',
    mb: 'MB',
  },

  // Errores
  errors: {
    networkError: 'Error de conexión con el servidor. Verifique que el backend esté ejecutándose.',
    folderNotFound: 'La ruta especificada no existe.',
    folderNotDir: 'La ruta especificada no es un directorio.',
    folderNoPermission: 'No tiene permisos de lectura sobre la carpeta.',
    unknownError: 'Ocurrió un error inesperado.',
  },
} as const;

export default es;
