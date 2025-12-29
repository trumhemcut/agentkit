// Component model
export interface A2UIComponent {
  id: string;
  component: Record<string, any>;
}

// Component-specific prop types
export interface CheckboxProps {
  label?: { literalString?: string; path?: string };
  value?: { path?: string };
}

export interface ButtonProps {
  label?: { literalString?: string; path?: string };
  variant?: 'default' | 'destructive' | 'outline' | 'secondary' | 'ghost' | 'link';
  onClick?: { action?: string };
}

export interface TextProps {
  content?: { literalString?: string; path?: string };
  style?: 'body' | 'heading' | 'caption' | 'code';
  size?: 'sm' | 'md' | 'lg' | 'xl';
}

export interface InputProps {
  label?: { literalString?: string; path?: string };
  placeholder?: { literalString?: string; path?: string };
  value?: { path?: string };
  type?: 'text' | 'email' | 'password' | 'number';
}

export interface TextInputProps {
  label?: { literalString?: string; path?: string };
  placeholder?: { literalString?: string; path?: string };
  value?: { path?: string };
  multiline?: boolean;
}

export interface BarChartProps {
  title: { literalString: string };
  description?: { literalString: string };
  dataKeys: { literalString: string };
  colors?: { literalMap: Record<string, string> };
  data: { path: string };
}

export interface OTPInputProps {
  title?: { literalString?: string; path?: string };
  description?: { literalString?: string; path?: string };
  maxLength?: number;
  groups?: Array<{ start: number; end: number }>;
  patternType?: 'digits' | 'alphanumeric';
  buttonText?: { literalString?: string; path?: string };
  disabled?: boolean;
  value?: { path?: string };
}

export interface ContainerProps {
  children?: string[];
}

// Component type definitions
export type ComponentType = 
  | { Checkbox: CheckboxProps }
  | { Button: ButtonProps }
  | { Text: TextProps }
  | { Input: InputProps }
  | { TextInput: TextInputProps }
  | { BarChart: BarChartProps }
  | { OTPInput: OTPInputProps }
  | { Row: ContainerProps }
  | { Column: ContainerProps }
  | { Card: ContainerProps };

// Data model type
export type A2UIDataModel = Record<string, any>;

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

export interface UserAction {
  type: "userAction";
  surfaceId: string;
  actionName: string;
  context: Record<string, any>;
}

export type A2UIMessage = 
  | SurfaceUpdate 
  | DataModelUpdate 
  | BeginRendering 
  | DeleteSurface
  | UserAction;

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
