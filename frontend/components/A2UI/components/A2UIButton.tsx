import React from 'react';
import { Button } from '@/components/ui/button';
import { resolvePath } from '@/types/a2ui';

interface A2UIButtonProps {
  id: string;
  props: {
    label?: { literalString?: string; path?: string };
    variant?: 'default' | 'destructive' | 'outline' | 'secondary' | 'ghost' | 'link';
    onClick?: { action?: string };
  };
  dataModel: Record<string, any>;
  surfaceId: string;
  onAction?: (actionName: string, context: Record<string, any>) => void;
}

export const A2UIButton: React.FC<A2UIButtonProps> = ({
  id,
  props,
  dataModel,
  surfaceId,
  onAction
}) => {
  // Resolve label (literal or from data model)
  const labelText = props.label?.literalString || 
    resolvePath(dataModel, props.label?.path) || 
    'Button';
  
  const variant = props.variant || 'default';
  
  // Handle button click
  const handleClick = () => {
    if (props.onClick?.action && onAction) {
      onAction(props.onClick.action, {
        buttonId: id,
        surfaceId,
        timestamp: new Date().toISOString()
      });
    }
  };
  
  return (
    <Button
      id={id}
      variant={variant}
      onClick={handleClick}
      className="my-2"
    >
      {labelText}
    </Button>
  );
};
