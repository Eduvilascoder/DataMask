import React, { useEffect, useState } from 'react';
import {
  Container,
  Header,
  SpaceBetween,
  Button,
  Alert,
  Flashbar,
  Toggle,
  Input,
  FormField,
  Box,
  Modal,
  RadioGroup,
  Textarea,
} from '@cloudscape-design/components';

interface TypeEntry {
  enabled: boolean;
  label: string;
  description: string;
  pattern?: string;
  note?: string;
}

interface CustomType {
  id: string;
  enabled: boolean;
  label: string;
  description: string;
  pattern?: string;
}

interface FullConfig {
  version: number;
  types: Record<string, TypeEntry>;
  custom_types: CustomType[];
  updated_at: string | null;
  engine?: string;
  ollama_prompt?: string;
}

interface EngineStatus {
  ollama: { available: boolean; model: string; url: string };
  spacy: { available: boolean; model: string };
  active_engine: string;
}

const DEFAULT_OLLAMA_PROMPT = `Analiza el siguiente texto y extrae TODOS los datos personales sensibles.

Devuelve SOLO un JSON array con los datos encontrados. Cada elemento debe tener:
- "text": el texto exacto encontrado (tal cual aparece)
- "type": uno de: NOMBRE, DIRECCION

Reglas:
- NOMBRE: nombres completos de personas (nombre + apellido). Incluye nombres en MAYÚSCULAS.
- DIRECCION: direcciones postales, ciudades con país (ej: "Santiago, Chile"), calles con número.
- NO incluyas: títulos de cargo, nombres de empresas, tecnologías, idiomas.
- Si no hay datos sensibles, devuelve un array vacío: []

Texto a analizar:
---
{text}
---

Responde SOLO con el JSON array, sin explicaciones:`;

const ConfigPage: React.FC = () => {
  const [config, setConfig] = useState<FullConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [newTypeLabel, setNewTypeLabel] = useState('');
  const [newTypeDesc, setNewTypeDesc] = useState('');
  const [newTypePattern, setNewTypePattern] = useState('');
  const [engineStatus, setEngineStatus] = useState<EngineStatus | null>(null);
  const [flashMessages, setFlashMessages] = useState<Array<{
    type: 'success' | 'error';
    content: string;
    id: string;
    dismissible: boolean;
  }>>([]);

  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const response = await fetch('/api/config');
        const data = await response.json();
        // Handle v1 format migration
        if (!data.version || data.version < 2) {
          const types: Record<string, TypeEntry> = {};
          const oldTypes = data.types || data;
          const defaultDescs: Record<string, string> = {
            nombre: 'Detecta nombres y apellidos de personas',
            email: 'Detecta direcciones de correo electrónico',
            celular: 'Detecta números de celular con prefijo +54 9',
            telefono: 'Detecta números de teléfono fijo con prefijo +54',
            direccion: 'Detecta direcciones postales',
            tarjeta_credito: 'Detecta números de tarjeta de crédito (16 dígitos)',
            cuenta_bancaria: 'Detecta números de CBU (22 dígitos)',
            dni: 'Detecta números de DNI argentino (7-8 dígitos)',
            cuit_cuil: 'Detecta números de CUIT/CUIL (XX-XXXXXXXX-X)',
            pasaporte: 'Detecta números de pasaporte argentino (AAX######)',
          };
          for (const [key, val] of Object.entries(oldTypes)) {
            types[key] = {
              enabled: typeof val === 'boolean' ? val : (val as TypeEntry).enabled ?? true,
              label: key.toUpperCase(),
              description: defaultDescs[key] || '',
            };
          }
          setConfig({ version: 2, types, custom_types: [], updated_at: null, engine: 'ollama' });
        } else {
          setConfig({ engine: 'ollama', ...data } as FullConfig);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Error de red');
      } finally {
        setLoading(false);
      }
    };

    const fetchEngineStatus = async () => {
      try {
        const response = await fetch('/api/status/engine');
        if (response.ok) {
          const data: EngineStatus = await response.json();
          setEngineStatus(data);
        }
      } catch {
        // Silently fail
      }
    };

    fetchConfig();
    fetchEngineStatus();
  }, []);

  const handleToggle = (key: string, enabled: boolean) => {
    if (!config) return;
    const newTypes = { ...config.types, [key]: { ...config.types[key], enabled } };
    // Validate at least one active
    const anyActive = Object.values(newTypes).some(t => t.enabled) ||
      config.custom_types.some(ct => ct.enabled);
    if (!anyActive) {
      setFlashMessages([{
        type: 'error',
        content: 'Debe existir al menos 1 tipo activo.',
        id: 'min-type',
        dismissible: true,
      }]);
      return;
    }
    setConfig({ ...config, types: newTypes });
    setFlashMessages([]);
  };

  const handleDescriptionChange = (key: string, description: string) => {
    if (!config) return;
    const newTypes = { ...config.types, [key]: { ...config.types[key], description } };
    setConfig({ ...config, types: newTypes });
  };

  const handleCustomToggle = (index: number, enabled: boolean) => {
    if (!config) return;
    const newCustom = [...config.custom_types];
    newCustom[index] = { ...newCustom[index], enabled };
    const anyActive = Object.values(config.types).some(t => t.enabled) ||
      newCustom.some(ct => ct.enabled);
    if (!anyActive) {
      setFlashMessages([{
        type: 'error',
        content: 'Debe existir al menos 1 tipo activo.',
        id: 'min-type',
        dismissible: true,
      }]);
      return;
    }
    setConfig({ ...config, custom_types: newCustom });
  };

  const handleCustomDescChange = (index: number, description: string) => {
    if (!config) return;
    const newCustom = [...config.custom_types];
    newCustom[index] = { ...newCustom[index], description };
    setConfig({ ...config, custom_types: newCustom });
  };

  const handleDeleteCustom = (index: number) => {
    if (!config) return;
    const newCustom = config.custom_types.filter((_, i) => i !== index);
    setConfig({ ...config, custom_types: newCustom });
  };

  const handleAddType = () => {
    if (!config || !newTypeLabel.trim()) return;
    const id = newTypeLabel.trim().toLowerCase().replace(/\s+/g, '_');
    const newCustom: CustomType = {
      id,
      enabled: true,
      label: newTypeLabel.trim().toUpperCase(),
      description: newTypeDesc.trim() || `Detecta ${newTypeLabel.trim().toLowerCase()}`,
      pattern: newTypePattern.trim() || undefined,
    };
    setConfig({ ...config, custom_types: [...config.custom_types, newCustom] });
    setNewTypeLabel('');
    setNewTypeDesc('');
    setNewTypePattern('');
    setShowAddModal(false);
  };

  const handleEngineChange = (value: string) => {
    if (!config) return;
    setConfig({ ...config, engine: value });
  };

  const handleSave = async () => {
    if (!config) return;
    setSaving(true);
    setFlashMessages([]);
    try {
      const response = await fetch('/api/config', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
      });
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail?.message || 'Error al guardar');
      }
      setFlashMessages([{
        type: 'success',
        content: 'Configuración guardada correctamente.',
        id: 'save-ok',
        dismissible: true,
      }]);
    } catch (err) {
      setFlashMessages([{
        type: 'error',
        content: err instanceof Error ? err.message : 'Error al guardar',
        id: 'save-err',
        dismissible: true,
      }]);
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <Container><Alert type="info">Cargando configuración...</Alert></Container>;
  if (error) return <Container><Alert type="error">{error}</Alert></Container>;

  const ollamaDisabled = engineStatus ? !engineStatus.ollama.available : false;

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
          <Header variant="h2">
            Motor de IA
          </Header>
        }
      >
        <SpaceBetween size="s">
          {ollamaDisabled && (
            <Alert type="warning">
              Ollama no está disponible. Verifique que Ollama esté instalado y ejecutándose con el modelo llama3.1:8b.
            </Alert>
          )}
          <RadioGroup
            value={config?.engine || 'ollama'}
            onChange={({ detail }) => handleEngineChange(detail.value)}
            items={[
              {
                value: 'ollama',
                label: 'Ollama (Llama 3.1 8B)',
                description: 'Mayor precisión para nombres y direcciones. Requiere Ollama instalado.',
                disabled: ollamaDisabled,
              },
              {
                value: 'spacy',
                label: 'spaCy (es_core_news_lg)',
                description: 'Más rápido pero menos preciso con nombres en mayúsculas.',
              },
            ]}
          />
        </SpaceBetween>
      </Container>

      <Container
        header={
          <Header variant="h2">
            Prompt de Ollama
          </Header>
        }
      >
        <SpaceBetween size="s">
          <FormField
            description="Use {text} como placeholder para el texto del documento"
          >
            <Textarea
              value={config?.ollama_prompt ?? DEFAULT_OLLAMA_PROMPT}
              onChange={({ detail }) => {
                if (!config) return;
                setConfig({ ...config, ollama_prompt: detail.value });
              }}
              rows={12}
            />
          </FormField>
          <Button
            onClick={() => {
              if (!config) return;
              setConfig({ ...config, ollama_prompt: DEFAULT_OLLAMA_PROMPT });
            }}
          >
            Restaurar prompt por defecto
          </Button>
        </SpaceBetween>
      </Container>

      <Container
        header={
          <Header
            variant="h1"
            description="Configure qué tipos de datos sensibles detectar. Puede editar las descripciones y agregar tipos personalizados."
            actions={
              <SpaceBetween size="xs" direction="horizontal">
                <Button onClick={() => setShowAddModal(true)}>
                  Agregar tipo
                </Button>
                <Button variant="primary" onClick={handleSave} loading={saving}>
                  {saving ? 'Guardando...' : 'Guardar configuración'}
                </Button>
              </SpaceBetween>
            }
          >
            Configuración de tipos de datos sensibles
          </Header>
        }
      >
        <SpaceBetween size="m">
          {config && Object.entries(config.types).map(([key, typeEntry]) => (
            <Box key={key} padding={{ vertical: 'xs' }}>
              <SpaceBetween size="xs">
                <Toggle
                  checked={typeEntry.enabled}
                  onChange={({ detail }) => handleToggle(key, detail.checked)}
                >
                  <strong>[{typeEntry.label}]</strong>
                </Toggle>
                <Input
                  value={typeEntry.description}
                  onChange={({ detail }) => handleDescriptionChange(key, detail.value)}
                  placeholder="Descripción del tipo de dato..."
                />
                <FormField
                  label=""
                  description="Patrón regex (editable)"
                >
                  <Input
                    value={typeEntry.pattern || ''}
                    onChange={({ detail }) => {
                      if (!config) return;
                      const newTypes = { ...config.types, [key]: { ...config.types[key], pattern: detail.value } };
                      setConfig({ ...config, types: newTypes });
                    }}
                    placeholder="Expresión regular para este tipo..."
                  />
                </FormField>
              </SpaceBetween>
            </Box>
          ))}

          {config && config.custom_types.length > 0 && (
            <>
              <Header variant="h3">Tipos personalizados</Header>
              {config.custom_types.map((ct, index) => (
                <Box key={ct.id} padding={{ vertical: 'xs' }}>
                  <SpaceBetween size="xs">
                    <SpaceBetween size="xs" direction="horizontal">
                      <Toggle
                        checked={ct.enabled}
                        onChange={({ detail }) => handleCustomToggle(index, detail.checked)}
                      >
                        <strong>[{ct.label}]</strong>
                      </Toggle>
                      <Button
                        variant="icon"
                        iconName="remove"
                        onClick={() => handleDeleteCustom(index)}
                      />
                    </SpaceBetween>
                    <Input
                      value={ct.description}
                      onChange={({ detail }) => handleCustomDescChange(index, detail.value)}
                      placeholder="Descripción..."
                    />
                    <FormField label="" description="Patrón regex (editable)">
                      <Input
                        value={ct.pattern || ''}
                        onChange={({ detail }) => {
                          if (!config) return;
                          const newCustom = [...config.custom_types];
                          newCustom[index] = { ...newCustom[index], pattern: detail.value };
                          setConfig({ ...config, custom_types: newCustom });
                        }}
                        placeholder="Expresión regular para este tipo..."
                      />
                    </FormField>
                  </SpaceBetween>
                </Box>
              ))}
            </>
          )}
        </SpaceBetween>
      </Container>

      <Modal
        visible={showAddModal}
        onDismiss={() => setShowAddModal(false)}
        header="Agregar nuevo tipo de dato sensible"
        footer={
          <Box float="right">
            <SpaceBetween size="xs" direction="horizontal">
              <Button onClick={() => setShowAddModal(false)}>Cancelar</Button>
              <Button variant="primary" onClick={handleAddType} disabled={!newTypeLabel.trim()}>
                Agregar
              </Button>
            </SpaceBetween>
          </Box>
        }
      >
        <SpaceBetween size="m">
          <FormField label="Nombre del tipo (se usará como etiqueta [NOMBRE])">
            <Input
              value={newTypeLabel}
              onChange={({ detail }) => setNewTypeLabel(detail.value)}
              placeholder="Ej: NUMERO_LEGAJO"
            />
          </FormField>
          <FormField label="Descripción">
            <Input
              value={newTypeDesc}
              onChange={({ detail }) => setNewTypeDesc(detail.value)}
              placeholder="Ej: Detecta números de legajo de empleados"
            />
          </FormField>
          <FormField
            label="Patrón regex (opcional)"
            description="Expresión regular para detectar este tipo de dato"
          >
            <Input
              value={newTypePattern}
              onChange={({ detail }) => setNewTypePattern(detail.value)}
              placeholder="Ej: \bLEG-\d{6}\b"
            />
          </FormField>
        </SpaceBetween>
      </Modal>
    </SpaceBetween>
  );
};

export default ConfigPage;
