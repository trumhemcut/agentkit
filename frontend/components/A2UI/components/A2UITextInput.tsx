import React from 'react';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { useA2UIStore } from '@/stores/a2uiStore';
import { resolvePath } from '@/types/a2ui';

interface A2UITextInputProps {
  id: string;
  props: {
    label?: { literalString?: string; path?: string };
    placeholder?: { literalString?: string; path?: string };
    value?: { path?: string };
    multiline?: boolean;
  };
  dataModel: Record<string, any>;
  surfaceId: string;
}

export const A2UITextInput: React.FC<A2UITextInputProps> = ({
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
  
  const isMultiline = props.multiline || false;
  
  // Handle input/textarea change
  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const newValue = e.target.value;
    
    if (props.value?.path) {
      // Extract key from path (e.g., "/form/comments" → "comments")
      const pathParts = props.value.path.split('/').filter(p => p);
      const key = pathParts[pathParts.length - 1];
      const parentPath = '/' + pathParts.slice(0, -1).join('/');
      
      // Update data model
      updateDataModel(surfaceId, parentPath, [
        { key, valueString: newValue }
      ]);
      
      // TODO: Send userAction to backend
      // sendUserAction({ name: "textinput_changed", context: { [key]: newValue } })
    }
  };
  
  return (
    <div className="space-y-2 py-2">
      {labelText && (
        <Label htmlFor={id}>
          {labelText}
        </Label>
      )}
      {isMultiline ? (
        <Textarea
          id={id}
          value={value}
          onChange={handleChange}
          placeholder={placeholderText}
          rows={4}
          className="resize-y"
        />
      ) : (
        <Input
          id={id}
          type="text"
          value={value}
          onChange={handleChange}
          placeholder={placeholderText}
        />
      )}
    </div>
  );
};
