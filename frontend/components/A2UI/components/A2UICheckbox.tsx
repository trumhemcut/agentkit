import React from 'react';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { useA2UIStore } from '@/stores/a2uiStore';
import { resolvePath } from '@/types/a2ui';
import { a2uiManager } from '@/lib/a2ui/A2UIManager';

interface A2UICheckboxProps {
  id: string;
  props: {
    label?: { literalString?: string; path?: string };
    value?: { path?: string };
    onChange?: {
      name: string;
      context?: Record<string, any>;
    };
  };
  dataModel: Record<string, any>;
  surfaceId: string;
}

export const A2UICheckbox: React.FC<A2UICheckboxProps> = ({
  id,
  props,
  dataModel,
  surfaceId
}) => {
  const setValueAtPath = useA2UIStore((state) => state.setValueAtPath);
  
  // Resolve label (literal or from data model)
  const labelText = props.label?.literalString || 
    resolvePath(dataModel, props.label?.path) || 
    'Checkbox';
  
  // Resolve value from data model
  const checked = resolvePath(dataModel, props.value?.path) || false;
  
  // Handle checkbox change
  const handleChange = (newValue: boolean | string) => {
    const boolValue = typeof newValue === 'boolean' ? newValue : newValue === 'on';
    
    if (props.value?.path) {
      // Two-way binding: update data model immediately
      setValueAtPath(surfaceId, props.value.path, boolValue);
      
      // If onChange action is defined, trigger it
      if (props.onChange) {
        a2uiManager.handleComponentAction(
          surfaceId,
          id,
          props.onChange.name,
          props.onChange.context || {}
        );
      }
    }
  };
  
  return (
    <div className="flex items-center space-x-2 py-2">
      <Checkbox
        id={id}
        checked={checked}
        onCheckedChange={handleChange}
      />
      <Label htmlFor={id} className="cursor-pointer">
        {labelText}
      </Label>
    </div>
  );
};
