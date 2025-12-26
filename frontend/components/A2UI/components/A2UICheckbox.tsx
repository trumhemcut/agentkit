import React from 'react';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { useA2UIStore } from '@/stores/a2uiStore';
import { resolvePath } from '@/types/a2ui';

interface A2UICheckboxProps {
  id: string;
  props: {
    label?: { literalString?: string; path?: string };
    value?: { path?: string };
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
  const updateDataModel = useA2UIStore((state) => state.updateDataModel);
  
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
      // Extract key from path (e.g., "/form/agreedToTerms" → "agreedToTerms")
      const pathParts = props.value.path.split('/').filter(p => p);
      const key = pathParts[pathParts.length - 1];
      const parentPath = '/' + pathParts.slice(0, -1).join('/');
      
      // Update data model
      updateDataModel(surfaceId, parentPath, [
        { key, valueBoolean: boolValue }
      ]);
      
      // TODO: Send userAction to backend
      // sendUserAction({ name: "checkbox_changed", context: { [key]: newValue } })
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
