# A2UI Quick Reference - Frontend

## Quick Start

### 1. Import A2UI Components

```typescript
import { A2UIRenderer } from '@/components/A2UI/A2UIRenderer';
import { useA2UIStore } from '@/stores/a2uiStore';
import { useA2UIEvents } from '@/hooks/useA2UIEvents';
import { isA2UIMessage } from '@/types/a2ui';
```

### 2. Process A2UI Events

```typescript
const { processA2UIMessage } = useA2UIEvents();

// In your event handler
if (isA2UIMessage(event)) {
  processA2UIMessage(event);
}
```

### 3. Render Surfaces

```typescript
const surfaces = useA2UIStore((state) => state.surfaces);
const surfaceIds = Array.from(surfaces.keys());

return (
  <>
    {surfaceIds.map((surfaceId) => (
      <A2UIRenderer key={surfaceId} surfaceId={surfaceId} />
    ))}
  </>
);
```

## Component Checklist

### Creating a New A2UI Component

1. **Create component file** in `components/A2UI/components/`
   ```typescript
   // A2UIButton.tsx
   import { Button } from '@/components/ui/button';
   import { useA2UIStore } from '@/stores/a2uiStore';
   import { resolvePath } from '@/types/a2ui';
   
   export const A2UIButton: React.FC<A2UIButtonProps> = ({ ... }) => {
     // Component logic
   };
   ```

2. **Add to renderer** in `A2UIRenderer.tsx`
   ```typescript
   case 'Button':
     return <A2UIButton key={id} {...props} />;
   ```

3. **Define TypeScript interface**
   ```typescript
   interface A2UIButtonProps {
     id: string;
     props: {
       label?: { literalString?: string; path?: string };
       onClick?: { action?: string };
     };
     dataModel: Record<string, any>;
     surfaceId: string;
   }
   ```

4. **Implement data binding**
   ```typescript
   const labelText = props.label?.literalString || 
     resolvePath(dataModel, props.label?.path);
   ```

5. **Handle user interactions**
   ```typescript
   const handleClick = () => {
     // TODO: Send userAction to backend
     console.log('Button clicked:', props.onClick?.action);
   };
   ```

## Common Patterns

### Reading from Data Model

```typescript
import { resolvePath } from '@/types/a2ui';

const value = resolvePath(dataModel, '/path/to/value');
```

### Writing to Data Model

```typescript
import { useA2UIStore } from '@/stores/a2uiStore';

const updateDataModel = useA2UIStore((state) => state.updateDataModel);

updateDataModel(surfaceId, '/path', [
  { key: 'fieldName', valueString: 'new value' }
]);
```

### Conditional Rendering

```typescript
const isVisible = resolvePath(dataModel, '/ui/showPanel');

if (!isVisible) return null;

return <div>...</div>;
```

### Dynamic Styling

```typescript
const theme = resolvePath(dataModel, '/settings/theme');
const className = theme === 'dark' ? 'bg-gray-800' : 'bg-white';

return <div className={className}>...</div>;
```

## Message Examples

### Simple Checkbox

```json
{
  "type": "surfaceUpdate",
  "surfaceId": "form-1",
  "components": [
    {
      "id": "agree",
      "component": {
        "Checkbox": {
          "label": { "literalString": "I agree to terms" },
          "value": { "path": "/form/agreed" }
        }
      }
    }
  ]
}
```

```json
{
  "type": "dataModelUpdate",
  "surfaceId": "form-1",
  "path": "/form",
  "contents": [
    { "key": "agreed", "valueBoolean": false }
  ]
}
```

```json
{
  "type": "beginRendering",
  "surfaceId": "form-1",
  "rootComponentId": "agree"
}
```

### Form with Multiple Fields

```json
{
  "type": "surfaceUpdate",
  "surfaceId": "user-form",
  "components": [
    {
      "id": "form-card",
      "component": {
        "Card": {
          "children": ["name-input", "email-input", "submit-button"]
        }
      }
    },
    {
      "id": "name-input",
      "component": {
        "Input": {
          "label": { "literalString": "Name" },
          "value": { "path": "/user/name" },
          "placeholder": { "literalString": "Enter your name" }
        }
      }
    }
  ]
}
```

## Debugging

### Enable Console Logs

A2UI events are logged automatically:

```
[A2UI] Processing surfaceUpdate: {...}
[A2UI] Processing dataModelUpdate: {...}
[A2UI] Processing beginRendering: {...}
```

### Inspect Store State

```typescript
// In browser console
useA2UIStore.getState().surfaces
```

### Check Surface Status

```typescript
const surface = useA2UIStore.getState().getSurface('surface-id');
console.log('Is rendering?', surface?.isRendering);
console.log('Root component:', surface?.rootComponentId);
console.log('Components:', surface?.components);
console.log('Data model:', surface?.dataModel);
```

### Common Issues

| Issue | Solution |
|-------|----------|
| Surface not visible | Check `beginRendering` was received and `isRendering` is true |
| Component not found | Verify component ID matches between `components` and `rootComponentId` |
| Data not updating | Check path syntax and ensure data model is initialized |
| Unknown component type | Add component case to `A2UIRenderer.tsx` |

## Type Reference

### A2UIMessage Types

```typescript
type A2UIMessage = 
  | SurfaceUpdate 
  | DataModelUpdate 
  | BeginRendering 
  | DeleteSurface;
```

### Component Definition

```typescript
interface A2UIComponent {
  id: string;
  component: Record<string, any>;
}
```

### Data Model Contents

```typescript
interface DataContent {
  key: string;
  valueString?: string;
  valueNumber?: number;
  valueBoolean?: boolean;
  valueMap?: Record<string, any>;
}
```

## File Structure

```
frontend/
├── types/
│   └── a2ui.ts                    # Type definitions
├── stores/
│   └── a2uiStore.ts              # State management
├── hooks/
│   └── useA2UIEvents.ts          # Event processing
└── components/
    └── A2UI/
        ├── A2UIRenderer.tsx      # Main renderer
        └── components/
            ├── A2UICheckbox.tsx  # Checkbox component
            ├── A2UIButton.tsx    # (Add new components here)
            └── ...
```

## Next Steps

1. **Test with backend**: Ensure backend sends A2UI messages
2. **Add more components**: Create Button, Input, Dropdown, etc.
3. **Implement user actions**: Send interactions back to backend
4. **Add validation**: Client-side form validation
5. **Optimize performance**: Lazy rendering, memoization

## Resources

- [Full Documentation](./a2ui-integration.md)
- [Implementation Plan](../../1-implementation-plans/017-support-a2ui-protocol-plan.md)
- [A2UI Specification](https://a2ui.org/)
