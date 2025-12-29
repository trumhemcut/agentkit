# A2UI Dynamic Components - Frontend Reference

## Overview

The frontend supports **dynamic A2UI component rendering** with multiple component types. The backend LLM agent generates component specifications using tool calling, and the frontend renders them as native Shadcn UI components with full interactivity.

**Last Updated**: December 30, 2025  
**Implementation Plan**: [018-support-dynamic-frontend-components-plan.md](../../1-implementation-plans/018-support-dynamic-frontend-components-plan.md)

## Architecture

### Component Flow

```
Backend LLM Agent
    ↓ (Analyzes user prompt)
Tool Calling (CheckboxTool, ButtonTool, etc.)
    ↓ (Generates A2UI JSON)
A2UI Protocol Messages (SSE Stream)
    ↓ (surfaceUpdate, dataModelUpdate, beginRendering)
Frontend A2UIRenderer
    ↓ (Maps to React components)
Shadcn UI Components
    ↓ (User interactions)
User Action Callbacks → Backend
```

### Component Registry

| Component Type | Description | Shadcn UI Base | Interactive |
|---------------|-------------|----------------|-------------|
| **Checkbox** | Boolean toggle | `Checkbox` + `Label` | ✅ Yes |
| **Button** | Clickable action | `Button` | ✅ Yes |
| **Text** | Static/dynamic text | `<p>`, `<h3>`, `<code>` | ❌ No |
| **Input** | Text/number input | `Input` + `Label` | ✅ Yes |
| **OTPInput** | OTP verification code | `InputOTP` components | ✅ Yes |
| **Row** | Horizontal container | `<div>` with flexbox | ❌ No |
| **Column** | Vertical container | `<div>` with flexbox | ❌ No |
| **Card** | Bordered container | `<div>` with styling | ❌ No |

## Component Specifications

### 1. Checkbox Component

**Purpose**: Boolean selection with two-way data binding

**A2UI Schema**:
```json
{
  "id": "checkbox-abc123",
  "component": {
    "Checkbox": {
      "label": { "literalString": "I agree to terms" },
      "value": { "path": "/form/agreedToTerms" }
    }
  }
}
```

**TypeScript Props**:
```typescript
interface CheckboxProps {
  label?: { literalString?: string; path?: string };
  value?: { path?: string };
}
```

**Data Model**:
```json
{
  "path": "/form",
  "contents": [
    { "key": "agreedToTerms", "valueBoolean": false }
  ]
}
```

**Features**:
- ✅ Two-way data binding via JSON Pointer paths
- ✅ Updates data model on user click
- ✅ Supports literal or dynamic labels from data model
- ✅ Accessible with proper label association

**Example Usage**:
```typescript
// User clicks checkbox → Updates data model
// Data model: { form: { agreedToTerms: true } }
```

---

### 2. Button Component

**Purpose**: Trigger actions on click

**A2UI Schema**:
```json
{
  "id": "submit-button",
  "component": {
    "Button": {
      "label": { "literalString": "Submit Form" },
      "variant": "default",
      "onClick": { "action": "submit_form" }
    }
  }
}
```

**TypeScript Props**:
```typescript
interface ButtonProps {
  label?: { literalString?: string; path?: string };
  variant?: 'default' | 'destructive' | 'outline' | 'secondary' | 'ghost' | 'link';
  onClick?: { action?: string };
}
```

**Variants**:
- `default`: Primary button (blue)
- `destructive`: Danger action (red)
- `outline`: Bordered button
- `secondary`: Muted button
- `ghost`: Transparent button
- `link`: Text link style

**Action Callback**:
```typescript
// When clicked, sends userAction to backend:
{
  type: "userAction",
  surfaceId: "surface-abc",
  actionName: "submit_form",
  context: {
    buttonId: "submit-button",
    timestamp: "2025-12-27T10:30:00Z"
  }
}
```

**Features**:
- ✅ Shadcn UI button variants
- ✅ Sends action events to backend
- ✅ Dynamic label from data model or literal
- ✅ Accessible with proper ARIA attributes

---

### 3. Text Component

**Purpose**: Display static or dynamic text content

**A2UI Schema**:
```json
{
  "id": "greeting-text",
  "component": {
    "Text": {
      "content": { "literalString": "Welcome to AgentKit!" },
      "style": "heading",
      "size": "lg"
    }
  }
}
```

**TypeScript Props**:
```typescript
interface TextProps {
  content?: { literalString?: string; path?: string };
  style?: 'body' | 'heading' | 'caption' | 'code';
  size?: 'sm' | 'md' | 'lg' | 'xl';
}
```

**Styles**:
- `body`: Regular paragraph text
- `heading`: Bold heading text (renders as `<h3>`)
- `caption`: Muted small text (for hints/captions)
- `code`: Monospace code text with background

**Sizes**:
- `sm`: Small text (14px)
- `md`: Medium text (16px) - default
- `lg`: Large text (18px)
- `xl`: Extra large text (20px)

**Dynamic Content**:
```json
{
  "content": { "path": "/user/name" }
}
// Reads from data model: { user: { name: "Alice" } }
```

**Features**:
- ✅ Multiple styles (body, heading, caption, code)
- ✅ Configurable sizes
- ✅ Dynamic content from data model
- ✅ Semantic HTML elements

---

### 4. Input Component

**Purpose**: Text/number input with data binding

**A2UI Schema**:
```json
{
  "id": "email-input",
  "component": {
    "Input": {
      "label": { "literalString": "Email Address" },
      "placeholder": { "literalString": "user@example.com" },
      "value": { "path": "/form/email" },
      "type": "email"
    }
  }
}
```

**TypeScript Props**:
```typescript
interface InputProps {
  label?: { literalString?: string; path?: string };
  placeholder?: { literalString?: string; path?: string };
  value?: { path?: string };
  type?: 'text' | 'email' | 'password' | 'number';
}
```

**Input Types**:
- `text`: Plain text input (default)
- `email`: Email with browser validation
- `password`: Masked password input
- `number`: Numeric input with spinners

**Data Model**:
```json
{
  "path": "/form",
  "contents": [
    { "key": "email", "valueString": "" }
  ]
}
```

**Features**:
- ✅ Two-way data binding
- ✅ Real-time updates to data model on change
- ✅ HTML5 input types with validation
- ✅ Optional label and placeholder
- ✅ Accessible with proper label association

**Number Input**:
```json
{
  "type": "number",
  "value": { "path": "/form/age" }
}
// Data model uses valueNumber instead of valueString
```

---

### 5. OTPInput Component

**Purpose**: One-Time Password (OTP) verification code input with configurable length and separators

**A2UI Schema**:
```json
{
  "id": "otp-a1b2c3",
  "component": {
    "OTPInput": {
      "title": { "literalString": "Verify your email" },
      "description": { "literalString": "Enter the 6-digit code sent to your email" },
      "maxLength": 6,
      "groups": [
        { "start": 0, "end": 3 },
        { "start": 3, "end": 6 }
      ],
      "patternType": "digits",
      "buttonText": { "literalString": "Verify" },
      "disabled": false,
      "value": { "path": "/ui/otp-a1b2c3/value" }
    }
  }
}
```

**TypeScript Props**:
```typescript
interface OTPInputProps {
  title?: { literalString?: string; path?: string };
  description?: { literalString?: string; path?: string };
  maxLength?: number;
  groups?: Array<{ start: number; end: number }>;
  patternType?: 'digits' | 'alphanumeric';
  buttonText?: { literalString?: string; path?: string };
  disabled?: boolean;
  value?: { path?: string };
}
```

**Configuration Options**:

**maxLength**: Number of OTP characters (default: 6)
```json
{ "maxLength": 4 }  // 4-digit code
{ "maxLength": 6 }  // 6-digit code (default)
```

**groups**: Array of slot groups with separators
```json
// Single group (no separators): 123456
{ "groups": [{ "start": 0, "end": 6 }] }

// Two groups with separator: 123-456
{ "groups": [
  { "start": 0, "end": 3 },
  { "start": 3, "end": 6 }
]}

// Three groups with separators: 12-34-56
{ "groups": [
  { "start": 0, "end": 2 },
  { "start": 2, "end": 4 },
  { "start": 4, "end": 6 }
]}
```

**patternType**: Input validation pattern
```json
{ "patternType": "digits" }        // 0-9 only (default)
{ "patternType": "alphanumeric" }  // 0-9, A-Z, a-z
```

**Data Model**:
```json
{
  "path": "/ui/otp-a1b2c3",
  "contents": [
    { "key": "value", "valueString": "" }  // Initially empty
  ]
}

// After user enters code:
{
  "path": "/ui/otp-a1b2c3",
  "contents": [
    { "key": "value", "valueString": "123456" }
  ]
}
```

**Features**:
- ✅ Configurable code length (4, 5, 6, or custom)
- ✅ Flexible separator grouping
- ✅ Digits-only or alphanumeric validation
- ✅ Two-way data binding with data model
- ✅ Button disabled until code complete
- ✅ Real-time value display
- ✅ User action callback on submit
- ✅ Disabled state support
- ✅ Accessible with ARIA attributes

**Example Scenarios**:

**Email Verification (6 digits)**:
```json
{
  "title": { "literalString": "Verify your email" },
  "description": { "literalString": "Enter the 6-digit code sent to your email" },
  "maxLength": 6,
  "groups": [{ "start": 0, "end": 6 }]
}
```

**Two-Factor Authentication (6 digits with separator)**:
```json
{
  "title": { "literalString": "Two-Factor Authentication" },
  "description": { "literalString": "Enter the code from your authenticator app" },
  "maxLength": 6,
  "groups": [
    { "start": 0, "end": 3 },
    { "start": 3, "end": 6 }
  ]
}
```

**Phone Verification (4 digits with separator)**:
```json
{
  "title": { "literalString": "Verify your phone" },
  "description": { "literalString": "Enter the 4-digit code sent via SMS" },
  "maxLength": 4,
  "groups": [
    { "start": 0, "end": 2 },
    { "start": 2, "end": 4 }
  ]
}
```

**Action Callback**:
```typescript
// When user clicks verify button, sends userAction to backend:
{
  type: "userAction",
  surfaceId: "surface-abc",
  actionName: "otp_submit",
  context: {
    componentId: "otp-a1b2c3",
    value: "123456",
    path: "/ui/otp-a1b2c3/value"
  }
}
```

**Implementation**:
- Component: `components/A2UI/components/A2UIOTPInput.tsx`
- Uses Shadcn UI `InputOTP`, `InputOTPGroup`, `InputOTPSlot`, `InputOTPSeparator`
- Pattern validation via `input-otp` library (`REGEXP_ONLY_DIGITS`, `REGEXP_ONLY_DIGITS_AND_CHARS`)
- Fully controlled component with React state
- See [Implementation Plan 023](../../1-implementation-plans/023-support-otp-plan.md)

---

### 6. Container Components (Row, Column, Card)

**Purpose**: Layout and grouping of child components

#### Row (Horizontal Layout)

```json
{
  "id": "button-row",
  "component": {
    "Row": {
      "children": ["button-1", "button-2", "button-3"]
    }
  }
}
```

**Renders as**: `<div className="flex flex-row gap-4">`

#### Column (Vertical Layout)

```json
{
  "id": "form-column",
  "component": {
    "Column": {
      "children": ["input-1", "input-2", "checkbox-1"]
    }
  }
}
```

**Renders as**: `<div className="flex flex-col gap-2">`

#### Card (Bordered Container)

```json
{
  "id": "info-card",
  "component": {
    "Card": {
      "children": ["text-1", "button-1"]
    }
  }
}
```

**Renders as**: `<div className="border rounded-lg p-4 shadow-sm">`

**Features**:
- ✅ Recursive child rendering
- ✅ Responsive Tailwind CSS layouts
- ✅ Nested containers supported

---

## User Action System

### Overview

User interactions (button clicks, input changes, checkbox toggles) are sent back to the backend as **userAction** messages.

### Action Service

**File**: `services/a2uiActionService.ts`

```typescript
export class A2UIActionService {
  async sendUserAction(
    surfaceId: string,
    actionName: string,
    context: Record<string, any>,
    threadId?: string
  ): Promise<void>
}
```

### Action Message Format

```typescript
{
  type: "userAction",
  surfaceId: "surface-abc",
  actionName: "button_clicked",
  context: {
    buttonId: "submit-btn",
    surfaceId: "surface-abc",
    threadId: "thread-123",
    timestamp: "2025-12-27T10:30:00Z"
  }
}
```

### Backend Endpoint

**POST** `/api/a2ui/action`

**Request Body**:
```json
{
  "type": "userAction",
  "surfaceId": "surface-abc",
  "actionName": "submit_form",
  "context": { ... }
}
```

**Response**: `200 OK` (no body)

### Integration Flow

```typescript
// 1. AgentMessageBubble creates callback
const handleA2UIAction = a2uiActionService.createActionCallback(threadId);

// 2. Pass to A2UIRenderer
<A2UIRenderer surfaceId={surfaceId} onAction={handleA2UIAction} />

// 3. A2UIButton uses callback
<A2UIButton {...props} onAction={onAction} />

// 4. User clicks button → Action sent to backend
```

---

## A2UIRenderer Implementation

### Component Mapping

**File**: `components/A2UI/A2UIRenderer.tsx`

```typescript
const renderComponent = (componentId: string): React.ReactNode => {
  const component = surface.components.get(componentId);
  const [componentType, props] = Object.entries(component.component)[0];
  
  switch (componentType) {
    case 'Checkbox':
      return <A2UICheckbox {...props} />;
    case 'Button':
      return <A2UIButton {...props} onAction={onAction} />;
    case 'Text':
      return <A2UIText {...props} />;
    case 'Input':
      return <A2UIInput {...props} />;
    case 'Row':
      return (
        <div className="flex flex-row gap-4">
          {props.children?.map(renderComponent)}
        </div>
      );
    // ... more cases
  }
};
```

### Recursive Rendering

Container components recursively render their children:

```typescript
<div className="flex flex-col gap-2">
  {props.children?.map((childId: string) => renderComponent(childId))}
</div>
```

### Error Handling

Unknown components show fallback message:

```typescript
default:
  console.warn(`[A2UI] Unknown component type: ${componentType}`);
  return (
    <div className="text-muted-foreground text-sm">
      Unsupported component: {componentType}
    </div>
  );
```

---

## Data Model Management

### Store Structure

**File**: `stores/a2uiStore.ts`

```typescript
interface Surface {
  id: string;
  components: Map<string, A2UIComponent>;
  dataModel: Record<string, any>;
  rootComponentId?: string;
  isRendering: boolean;
  messageId?: string;
}
```

### JSON Pointer Paths

A2UI uses JSON Pointer (RFC 6901) for data paths:

```
/form/user/email   → dataModel.form.user.email
/settings/theme    → dataModel.settings.theme
/agreedToTerms     → dataModel.agreedToTerms
```

### Data Updates

**On User Interaction**:

```typescript
// Checkbox changed
updateDataModel(surfaceId, "/form", [
  { key: "agreedToTerms", valueBoolean: true }
]);

// Input changed
updateDataModel(surfaceId, "/form", [
  { key: "email", valueString: "user@example.com" }
]);

// Number input changed
updateDataModel(surfaceId, "/form", [
  { key: "age", valueNumber: 25 }
]);
```

### Path Resolution

**Helper Function**:

```typescript
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
```

---

## Component Files

### File Structure

```
frontend/
├── components/
│   └── A2UI/
│       ├── A2UIRenderer.tsx       # Main renderer
│       └── components/
│           ├── A2UICheckbox.tsx   # Checkbox component
│           ├── A2UIButton.tsx     # Button component
│           ├── A2UIText.tsx       # Text component
│           ├── A2UIInput.tsx      # Input component
│           └── A2UIOTPInput.tsx   # OTP input component
├── types/
│   └── a2ui.ts                    # Type definitions
├── stores/
│   └── a2uiStore.ts               # State management
├── hooks/
│   └── useA2UIEvents.ts           # Event processing
└── services/
    └── a2uiActionService.ts       # User action handling
```

### Component Imports

```typescript
// In A2UIRenderer.tsx
import { A2UICheckbox } from './components/A2UICheckbox';
import { A2UIButton } from './components/A2UIButton';
import { A2UIText } from './components/A2UIText';
import { A2UIInput } from './components/A2UIInput';
import { A2UIOTPInput } from './components/A2UIOTPInput';
```

---

## Styling Guide

### Shadcn UI Integration

All components use Shadcn UI primitives for consistency:

```typescript
// Checkbox
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';

// Button
import { Button } from '@/components/ui/button';

// Input
import { Input } from '@/components/ui/input';

// OTP Input
import {
  InputOTP,
  InputOTPGroup,
  InputOTPSlot,
  InputOTPSeparator,
} from '@/components/ui/input-otp';
```

### Tailwind CSS Classes

**Common Patterns**:

```typescript
// Spacing
className="py-2 my-2"           // Vertical padding/margin
className="space-x-2 gap-4"     // Horizontal spacing

// Layout
className="flex flex-row gap-4"  // Horizontal flex
className="flex flex-col gap-2"  // Vertical flex

// Styling
className="border rounded-lg p-4 shadow-sm"  // Card style
className="text-muted-foreground text-sm"    // Caption style
```

### Dark Mode Support

Shadcn UI components automatically support dark mode via Tailwind CSS:

```typescript
<Button variant="default">  // Adapts to light/dark theme
<Input />                   // Inherits theme colors
```

---

## Testing

### Unit Tests

**Test Component Rendering**:

```typescript
// Test checkbox renders with correct label
test('A2UICheckbox renders label', () => {
  const props = {
    label: { literalString: "Accept" }
  };
  render(<A2UICheckbox {...props} />);
  expect(screen.getByText("Accept")).toBeInTheDocument();
});
```

**Test Data Binding**:

```typescript
// Test input updates data model
test('A2UIInput updates on change', () => {
  const updateDataModel = jest.fn();
  render(<A2UIInput {...props} />);
  fireEvent.change(input, { target: { value: "test@example.com" } });
  expect(updateDataModel).toHaveBeenCalled();
});
```

### Integration Tests

**Test A2UI Flow**:

```typescript
// 1. Send A2UI messages
// 2. Verify components render
// 3. Interact with component
// 4. Verify action sent to backend
```

---

## Best Practices

### 1. Always Initialize Data Model

```json
// Before beginRendering, send dataModelUpdate
{
  "type": "dataModelUpdate",
  "surfaceId": "surface-abc",
  "path": "/",
  "contents": [
    { "key": "form", "valueMap": { "email": "", "agreed": false } }
  ]
}
```

### 2. Use Meaningful Component IDs

```json
// Good: Descriptive IDs
"id": "email-input"
"id": "submit-button"

// Bad: Generic IDs
"id": "component-1"
"id": "comp2"
```

### 3. Handle Missing Data Gracefully

```typescript
const labelText = props.label?.literalString || 
  resolvePath(dataModel, props.label?.path) || 
  'Default Label';  // Fallback
```

### 4. Log Component Rendering

```typescript
console.log(`[A2UI] Rendering ${componentType}:`, componentId);
```

### 5. Type Everything

```typescript
// Use TypeScript interfaces for props
interface A2UIButtonProps {
  id: string;
  props: ButtonProps;
  dataModel: Record<string, any>;
  surfaceId: string;
  onAction?: (actionName: string, context: Record<string, any>) => void;
}
```

---

## Troubleshooting

### Component Not Rendering

**Problem**: Component defined but doesn't appear

**Solutions**:
1. Check `beginRendering` message received
2. Verify component ID in `rootComponentId`
3. Check `surface.isRendering` is `true`
4. Verify component type matches case in switch statement

### Button Click Not Working

**Problem**: Button click doesn't trigger action

**Solutions**:
1. Check `onAction` prop passed to A2UIButton
2. Verify `onClick.action` defined in component props
3. Check action service endpoint URL is correct
4. Review network tab for failed requests

### Input Value Not Updating

**Problem**: Typing in input doesn't update UI

**Solutions**:
1. Verify `value.path` is valid JSON Pointer
2. Check data model has initial value for path
3. Ensure `updateDataModel` is called in onChange
4. Check browser console for errors

### Container Children Missing

**Problem**: Container renders but children don't

**Solutions**:
1. Verify `children` array has valid component IDs
2. Check child components exist in surface
3. Ensure recursive `renderComponent` is called
4. Check for infinite recursion (circular references)

---

## Future Enhancements

### Additional Components

- **Select/Dropdown**: Choose from options
- **Radio Buttons**: Single choice from group
- **Textarea**: Multi-line text input
- **Date Picker**: Date selection
- **Slider**: Numeric range selection
- **Toggle**: Boolean toggle switch
- **Table**: Tabular data display
- **Chart**: Data visualization

### Advanced Features

- **Form Validation**: Client-side validation with error messages
- **Conditional Rendering**: Show/hide based on data model
- **Animation**: Smooth transitions for UI updates
- **Drag & Drop**: Reorderable components
- **Custom Styling**: Theme overrides per component

---

## References

- [A2UI Protocol Spec](https://a2ui.org/specification/v0.8-a2ui/)
- [Shadcn UI Components](https://ui.shadcn.com/)
- [JSON Pointer RFC 6901](https://tools.ietf.org/html/rfc6901)
- [Implementation Plan 018](../../1-implementation-plans/018-support-dynamic-frontend-components-plan.md)
- [A2UI Integration Guide](./a2ui-integration.md)
