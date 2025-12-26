// Component model
export interface A2UIComponent {
  id: string;
  component: Record<string, any>;
}

// Message types
export interface SurfaceUpdate {
  type: "surfaceUpdate";
  surfaceId: string;
  components: A2UIComponent[];
}

export interface DataModelUpdate {
  type: "dataModelUpdate";
  surfaceId: string;
  path?: string;
  contents: Array<{
    key: string;
    valueString?: string;
    valueNumber?: number;
    valueBoolean?: boolean;
    valueMap?: Record<string, any>;
  }>;
}

export interface BeginRendering {
  type: "beginRendering";
  surfaceId: string;
  rootComponentId: string;
}

export interface DeleteSurface {
  type: "deleteSurface";
  surfaceId: string;
}

export type A2UIMessage = 
  | SurfaceUpdate 
  | DataModelUpdate 
  | BeginRendering 
  | DeleteSurface;

// Helper to check if a message is A2UI
export function isA2UIMessage(data: any): data is A2UIMessage {
  return data && typeof data === 'object' && [
    'surfaceUpdate',
    'dataModelUpdate',
    'beginRendering',
    'deleteSurface'
  ].includes(data.type);
}

// Helper to resolve JSON Pointer paths
export function resolvePath(obj: any, path?: string): any {
  if (!path) return undefined;
  
  const keys = path.split('/').filter(k => k);
  let current = obj;
  
  for (const key of keys) {
    if (current && typeof current === 'object' && key in current) {
      current = current[key];
    } else {
      return undefined;
    }
  }
  
  return current;
}
