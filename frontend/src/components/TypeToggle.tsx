import React from 'react';
import { Toggle, Box } from '@cloudscape-design/components';

interface TypeToggleProps {
  label: string;
  description: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  disabled?: boolean;
}

const TypeToggle: React.FC<TypeToggleProps> = ({
  label,
  description,
  checked,
  onChange,
  disabled = false,
}) => {
  return (
    <Box padding={{ vertical: 'xs' }}>
      <Toggle
        checked={checked}
        onChange={({ detail }) => onChange(detail.checked)}
        disabled={disabled}
      >
        <Box variant="strong">{label}</Box>
        <Box variant="small" color="text-body-secondary">
          {description}
        </Box>
      </Toggle>
    </Box>
  );
};

export default TypeToggle;
