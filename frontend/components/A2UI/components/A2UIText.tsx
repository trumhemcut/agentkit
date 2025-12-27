import React from 'react';
import { resolvePath } from '@/types/a2ui';

interface A2UITextProps {
  id: string;
  props: {
    content?: { literalString?: string; path?: string };
    style?: 'body' | 'heading' | 'caption' | 'code';
    size?: 'sm' | 'md' | 'lg' | 'xl';
  };
  dataModel: Record<string, any>;
  surfaceId: string;
}

export const A2UIText: React.FC<A2UITextProps> = ({
  id,
  props,
  dataModel,
  surfaceId
}) => {
  // Resolve text content (literal or from data model)
  const textContent = props.content?.literalString || 
    resolvePath(dataModel, props.content?.path) || 
    '';
  
  const style = props.style || 'body';
  const size = props.size || 'md';
  
  // Map style + size to Tailwind CSS classes
  const getClassName = () => {
    const baseClasses = 'my-2';
    
    const sizeClasses: Record<string, string> = {
      sm: 'text-sm',
      md: 'text-base',
      lg: 'text-lg',
      xl: 'text-xl'
    };
    
    const styleClasses: Record<string, string> = {
      body: '',
      heading: 'font-semibold',
      caption: 'text-muted-foreground text-sm',
      code: 'font-mono bg-muted px-1 py-0.5 rounded'
    };
    
    return `${baseClasses} ${sizeClasses[size]} ${styleClasses[style]}`;
  };
  
  if (style === 'heading') {
    return (
      <h3 id={id} className={getClassName()}>
        {textContent}
      </h3>
    );
  }
  
  if (style === 'code') {
    return (
      <code id={id} className={getClassName()}>
        {textContent}
      </code>
    );
  }
  
  return (
    <p id={id} className={getClassName()}>
      {textContent}
    </p>
  );
};
