import React from 'react';
import { Button } from '@/components/ui/button';
import { resolvePath } from '@/types/a2ui';
import { a2uiManager } from '@/lib/a2ui/A2UIManager';

interface A2UIButtonProps {
  id: string;
  props: {
    label?: { literalString?: string; path?: string };
    variant?: 'default' | 'destructive' | 'outline' | 'secondary' | 'ghost' | 'link';
    action?: {
      name: string;
      context?: Record<string, any>;
    };
    // Legacy support
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
  onAction // Keep for backward compatibility
}) => {
  // Resolve label (literal or from data model)
  const labelText = props.label?.literalString || 
    resolvePath(dataModel, props.label?.path) || 
    'Button';
  
  const variant = props.variant || 'default';
  
  // Handle button click
  const handleClick = () => {
    console.log('[A2UIButton] Button clicked', {
      id,
      surfaceId,
      action: props.action,
      legacyOnClick: props.onClick
    });
    
    // New A2UI v0.9 pattern: action object with name and context
    if (props.action) {
      console.log('[A2UIButton] Calling a2uiManager.handleComponentAction');
      a2uiManager.handleComponentAction(
        surfaceId,
        id,
        props.action.name,
        props.action.context || {}
      );
    }
    // Legacy support: onClick.action
    else if (props.onClick?.action) {
      console.log('[A2UIButton] Using legacy onClick pattern');
      if (onAction) {
        onAction(props.onClick.action, {
          buttonId: id,
          surfaceId,
          timestamp: new Date().toISOString()
        });
      } else {
        // Use new pattern
        a2uiManager.handleComponentAction(
          surfaceId,
          id,
          props.onClick.action,
          {}
        );
      }
    } else {
      console.warn('[A2UIButton] No action defined for button');
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
