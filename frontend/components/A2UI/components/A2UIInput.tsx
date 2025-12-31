import React from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useA2UIStore } from '@/stores/a2uiStore';
import { resolvePath } from '@/types/a2ui';

interface A2UIInputProps {
  id: string;
  props: {
    label?: { literalString?: string; path?: string };
    placeholder?: { literalString?: string; path?: string };
    value?: { path?: string };
    type?: 'text' | 'email' | 'password' | 'number';
  };
  dataModel: Record<string, any>;
  surfaceId: string;
}

export const A2UIInput: React.FC<A2UIInputProps> = ({
  id,
  props,
  dataModel,
  surfaceId
}) => {
  const setValueAtPath = useA2UIStore((state) => state.setValueAtPath);
  
  // Resolve label (literal or from data model)
  const labelText = props.label?.literalString || 
    resolvePath(dataModel, props.label?.path);
  
  // Resolve placeholder
  const placeholderText = props.placeholder?.literalString || 
    resolvePath(dataModel, props.placeholder?.path) || 
    '';
  
  // Resolve value from data model
  const value = resolvePath(dataModel, props.value?.path) || '';
  
  const inputType = props.type || 'text';
  
  // Handle input change - two-way binding updates data model immediately
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    
    if (props.value?.path) {
      // Convert to appropriate type
      const convertedValue = inputType === 'number' 
        ? parseFloat(newValue) || 0 
        : newValue;
      
      // Update data model using setValueAtPath
      setValueAtPath(surfaceId, props.value.path, convertedValue);
    }
  };
  
  return (
    <div className="space-y-2 py-2">
      {labelText && (
        <Label htmlFor={id}>
          {labelText}
        </Label>
      )}
      <Input
        id={id}
        type={inputType}
        value={value}
        onChange={handleChange}
        placeholder={placeholderText}
      />
    </div>
  );
};
