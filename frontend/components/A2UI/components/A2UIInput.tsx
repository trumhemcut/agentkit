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
  const updateDataModel = useA2UIStore((state) => state.updateDataModel);
  
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
  
  // Handle input change
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    
    if (props.value?.path) {
      // Extract key from path (e.g., "/form/email" → "email")
      const pathParts = props.value.path.split('/').filter(p => p);
      const key = pathParts[pathParts.length - 1];
      const parentPath = '/' + pathParts.slice(0, -1).join('/');
      
      // Update data model
      const updateContent = inputType === 'number'
        ? { key, valueNumber: parseFloat(newValue) || 0 }
        : { key, valueString: newValue };
      
      updateDataModel(surfaceId, parentPath, [updateContent]);
      
      // TODO: Send userAction to backend
      // sendUserAction({ name: "input_changed", context: { [key]: newValue } })
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
