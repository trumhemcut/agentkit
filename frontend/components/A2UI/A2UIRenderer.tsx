import React from 'react';
import { useA2UIStore } from '@/stores/a2uiStore';
import { A2UICheckbox } from './components/A2UICheckbox';
import { A2UIButton } from './components/A2UIButton';
import { A2UIText } from './components/A2UIText';
import { A2UIInput } from './components/A2UIInput';
import type { A2UIComponent } from '@/types/a2ui';

interface A2UIRendererProps {
  surfaceId: string;
  onAction?: (actionName: string, context: Record<string, any>) => void;
}

export const A2UIRenderer: React.FC<A2UIRendererProps> = ({ surfaceId, onAction }) => {
  const surface = useA2UIStore((state) => state.getSurface(surfaceId));
  
  if (!surface || !surface.isRendering || !surface.rootComponentId) {
    return null;
  }
  
  // Recursively render component tree starting from root
  const renderComponent = (componentId: string): React.ReactNode => {
    const component = surface.components.get(componentId);
    if (!component) {
      console.warn(`[A2UI] Component not found: ${componentId}`);
      return null;
    }
    
    // Get component type (first key in component object)
    const componentEntries = Object.entries(component.component);
    if (componentEntries.length === 0) {
      console.warn(`[A2UI] Component has no type: ${componentId}`);
      return null;
    }
    
    const [componentType, props] = componentEntries[0];
    
    // Map A2UI component types to React components
    switch (componentType) {
      case 'Checkbox':
        return (
          <A2UICheckbox
            key={component.id}
            id={component.id}
            props={props}
            dataModel={surface.dataModel}
            surfaceId={surfaceId}
          />
        );
      
      case 'Button':
        return (
          <A2UIButton
            key={component.id}
            id={component.id}
            props={props}
            dataModel={surface.dataModel}
            surfaceId={surfaceId}
            onAction={onAction}
          />
        );
      
      case 'Text':
        return (
          <A2UIText
            key={component.id}
            id={component.id}
            props={props}
            dataModel={surface.dataModel}
            surfaceId={surfaceId}
          />
        );
      
      case 'Input':
        return (
          <A2UIInput
            key={component.id}
            id={component.id}
            props={props}
            dataModel={surface.dataModel}
            surfaceId={surfaceId}
          />
        );
        
      // Add more component types as needed
      case 'Row':
        // Render horizontal container with children
        return (
          <div key={component.id} className="flex flex-row gap-4">
            {props.children?.map((childId: string) => renderComponent(childId))}
          </div>
        );
        
      case 'Column':
        // Render vertical container with children
        return (
          <div key={component.id} className="flex flex-col gap-2">
            {props.children?.map((childId: string) => renderComponent(childId))}
          </div>
        );
        
      case 'Card':
        // Render card container
        return (
          <div key={component.id} className="border rounded-lg p-4 shadow-sm">
            {props.children?.map((childId: string) => renderComponent(childId))}
          </div>
        );
        
      default:
        console.warn(`[A2UI] Unknown component type: ${componentType}`);
        return (
          <div key={component.id} className="text-muted-foreground text-sm">
            Unsupported component: {componentType}
          </div>
        );
    }
  };
  
  return (
    <div 
      className="a2ui-surface" 
      data-surface-id={surfaceId}
    >
      {renderComponent(surface.rootComponentId)}
    </div>
  );
};
