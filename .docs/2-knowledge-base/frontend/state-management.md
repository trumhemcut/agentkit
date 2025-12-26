# State Management with Zustand

**Last Updated**: December 26, 2025  
**Status**: Active  
**Migration**: Completed (from React hooks to Zustand)

## Overview

AgentKit uses [Zustand](https://github.com/pmndrs/zustand) for global state management. Zustand provides a lightweight, performant, and developer-friendly alternative to React Context with better performance through selective subscriptions.

## Why Zustand?

### Benefits
- ✅ **Performance**: Selective re-renders - components only update when their subscribed state changes
- ✅ **Simplicity**: No Provider wrappers needed - stores are global singletons
- ✅ **TypeScript**: Excellent type safety and inference
- ✅ **DevEx**: Clean, minimal API with less boilerplate
- ✅ **Persistence**: Built-in middleware for localStorage sync
- ✅ **Bundle Size**: ~3KB gzipped

### Comparison to React Context
| Feature | Zustand | React Context |
|---------|---------|---------------|
| Bundle Size | ~3KB | Included in React |
| Provider Wrappers | ❌ Not needed | ✅ Required |
| Selective Updates | ✅ Built-in | ❌ Manual optimization needed |
| Persistence | ✅ Middleware | 🔧 Custom implementation |
| Async Actions | ✅ Native support | 🔧 Custom hooks needed |
| DevTools | ✅ Available | ❌ Limited |

## Architecture

### Store Structure
```
frontend/
└── stores/
    ├── agentStore.ts      # Agent selection state
    └── modelStore.ts      # Model selection state
```

### Key Concepts

#### 1. Global Singletons
Stores are created once and accessed globally without Provider wrappers:
```typescript
// Create store
export const useAgentStore = create<AgentStore>()(...);

// Use in any component - no Provider needed!
const selectedAgent = useAgentStore((state) => state.selectedAgent);
```

#### 2. Selective Subscriptions
Components only re-render when their subscribed state changes:
```typescript
// ✅ Only re-renders when selectedAgent changes
const selectedAgent = useAgentStore((state) => state.selectedAgent);

// ❌ Re-renders on ANY store change
const store = useAgentStore();
```

#### 3. Persist Middleware
Automatically sync state to localStorage:
```typescript
persist(
  (set, get) => ({ /* store implementation */ }),
  {
    name: 'selected_agent',
    storage: createJSONStorage(() => localStorage),
    partialize: (state) => ({ selectedAgent: state.selectedAgent }),
  }
)
```

## Stores

### Agent Store

**File**: `frontend/stores/agentStore.ts`

**Purpose**: Manages agent selection and available agents

**State**:
```typescript
interface AgentStore {
  // State
  selectedAgent: string;
  availableAgents: AgentMetadata[];
  loading: boolean;
  error: string | null;
  
  // Actions
  setSelectedAgent: (agentId: string) => void;
  loadAgents: () => Promise<void>;
  reset: () => void;
}
```

**Features**:
- ✅ Persists `selectedAgent` to localStorage
- ✅ Auto-validates saved agent against available agents
- ✅ Async loading with error handling
- ✅ Console logging for debugging

**Usage**:
```typescript
import { useAgentStore, initializeAgentStore } from '@/stores/agentStore';

function AgentSelector() {
  // Auto-initialize on mount
  useEffect(() => {
    initializeAgentStore();
  }, []);

  // Selective subscriptions
  const selectedAgent = useAgentStore((state) => state.selectedAgent);
  const availableAgents = useAgentStore((state) => state.availableAgents);
  const setSelectedAgent = useAgentStore((state) => state.setSelectedAgent);
  const loading = useAgentStore((state) => state.loading);
  
  // ... component logic
}
```

### Model Store

**File**: `frontend/stores/modelStore.ts`

**Purpose**: Manages LLM model selection and available models

**State**:
```typescript
interface ModelStore {
  // State
  selectedModel: string | null;
  availableModels: LLMModel[];
  loading: boolean;
  error: string | null;
  
  // Actions
  setSelectedModel: (modelId: string) => void;
  loadModels: () => Promise<void>;
  getSelectedModelInfo: () => LLMModel | null;
  reset: () => void;
}
```

**Features**:
- ✅ Persists `selectedModel` to localStorage
- ✅ Validates model availability before selection
- ✅ Falls back to first available model if saved model is unavailable
- ✅ Helper method to get full model info

**Usage**:
```typescript
import { useModelStore, initializeModelStore } from '@/stores/modelStore';

function ModelSelector() {
  // Auto-initialize on mount
  useEffect(() => {
    initializeModelStore();
  }, []);

  // Selective subscriptions
  const selectedModel = useModelStore((state) => state.selectedModel);
  const availableModels = useModelStore((state) => state.availableModels);
  const setSelectedModel = useModelStore((state) => state.setSelectedModel);
  const loading = useModelStore((state) => state.loading);
  const selectedModelInfo = useModelStore((state) => state.getSelectedModelInfo());
  
  // ... component logic
}
```

## Usage Patterns

### Pattern 1: Selective Subscriptions (Recommended)
```typescript
// ✅ Component only re-renders when selectedAgent changes
const selectedAgent = useAgentStore((state) => state.selectedAgent);
const setSelectedAgent = useAgentStore((state) => state.setSelectedAgent);
```

**When to use**: Most cases - maximizes performance by preventing unnecessary re-renders

### Pattern 2: Multiple Subscriptions
```typescript
// Component re-renders when ANY subscribed field changes
const { selectedAgent, availableAgents, loading } = useAgentStore();
```

**When to use**: When you need multiple values and they all affect rendering

### Pattern 3: Access Outside Components
```typescript
// Get store state outside React components
const currentAgent = useAgentStore.getState().selectedAgent;

// Call actions directly
useAgentStore.getState().setSelectedAgent('chat');
```

**When to use**: Utility functions, middleware, or non-React code

### Pattern 4: Subscribe to Changes
```typescript
// Subscribe to store changes (returns unsubscribe function)
const unsubscribe = useAgentStore.subscribe(
  (state) => state.selectedAgent,
  (selectedAgent) => {
    console.log('Agent changed to:', selectedAgent);
  }
);

// Cleanup
unsubscribe();
```

**When to use**: Side effects, logging, analytics

## Initialization

### Auto-Initialization Pattern
Stores are initialized on first component mount using initialization functions:

```typescript
// stores/agentStore.ts
let hasInitialized = false;
export const initializeAgentStore = () => {
  if (hasInitialized) return;
  hasInitialized = true;
  useAgentStore.getState().loadAgents();
};

// components/AgentSelector.tsx
useEffect(() => {
  initializeAgentStore();
}, []);
```

**Why?**: Ensures data is loaded before it's needed without manual setup in layout

## Persistence

### LocalStorage Keys
- **Agent Store**: `selected_agent` (only persists `selectedAgent`)
- **Model Store**: `selected-llm-model` (only persists `selectedModel`)

### Partial Persistence
Only specific state fields are persisted using `partialize`:

```typescript
persist(
  (set, get) => ({ /* store */ }),
  {
    name: 'selected_agent',
    partialize: (state) => ({ 
      selectedAgent: state.selectedAgent 
      // availableAgents, loading, error are NOT persisted
    }),
  }
)
```

**Why?**: Avoid stale data - dynamic data like `availableAgents` is refreshed on load

## Performance Optimization

### 1. Selective Subscriptions
```typescript
// ✅ GOOD - Only re-renders when selectedAgent changes
const selectedAgent = useAgentStore((state) => state.selectedAgent);

// ❌ BAD - Re-renders on any store change
const store = useAgentStore();
```

### 2. Derived State
Use derived state instead of storing computed values:
```typescript
// In store
getSelectedModelInfo: () => {
  const { selectedModel, availableModels } = get();
  return availableModels.find(m => m.id === selectedModel) || null;
}

// In component
const selectedModelInfo = useModelStore((state) => state.getSelectedModelInfo());
```

### 3. Prevent Duplicate Loads
```typescript
loadAgents: async () => {
  const { loading } = get();
  if (loading) return; // Prevent duplicate loads
  
  try {
    set({ loading: true, error: null });
    // ... load data
  } catch (err) {
    // ... handle error
  }
}
```

## Debugging

### Console Logging
Stores include console logs for debugging:
```typescript
setSelectedAgent: (agentId: string) => {
  console.log('[AgentStore] Setting agent to:', agentId);
  set({ selectedAgent: agentId });
}
```

### Browser DevTools
1. **React DevTools**: View component re-renders
2. **Application → Local Storage**: Inspect persisted state
3. **Console**: Monitor store actions and state changes

### Zustand DevTools (Optional)
Install `zustand/middleware/devtools` for advanced debugging:
```typescript
import { devtools } from 'zustand/middleware';

export const useAgentStore = create<AgentStore>()(
  devtools(
    persist(
      (set, get) => ({ /* store */ }),
      { name: 'selected_agent' }
    ),
    { name: 'AgentStore' }
  )
);
```

## Migration Guide

### From React Hook to Zustand

**Before** (Hook):
```typescript
// hooks/useAgentSelection.ts
export function useAgentSelection() {
  const [selectedAgent, setSelectedAgentState] = useState<string>('');
  // ... hook logic
  return { selectedAgent, setSelectedAgent, ... };
}

// Component
import { useAgentSelection } from '@/hooks/useAgentSelection';
const { selectedAgent, setSelectedAgent } = useAgentSelection();
```

**After** (Zustand):
```typescript
// stores/agentStore.ts
export const useAgentStore = create<AgentStore>()(
  persist(
    (set, get) => ({
      selectedAgent: '',
      setSelectedAgent: (agentId: string) => set({ selectedAgent: agentId }),
      // ... store logic
    }),
    { name: 'selected_agent' }
  )
);

// Component
import { useAgentStore } from '@/stores/agentStore';
const selectedAgent = useAgentStore((state) => state.selectedAgent);
const setSelectedAgent = useAgentStore((state) => state.setSelectedAgent);
```

### From Context to Zustand

**Before** (Context):
```typescript
// contexts/AgentSelectionContext.tsx
const AgentSelectionContext = createContext<AgentStore | null>(null);

export function AgentSelectionProvider({ children }) {
  const [state, setState] = useState({...});
  return (
    <AgentSelectionContext.Provider value={{ state, setState }}>
      {children}
    </AgentSelectionContext.Provider>
  );
}

// app/layout.tsx
<AgentSelectionProvider>
  {children}
</AgentSelectionProvider>

// Component
const { selectedAgent } = useContext(AgentSelectionContext);
```

**After** (Zustand):
```typescript
// stores/agentStore.ts
export const useAgentStore = create<AgentStore>()(...)

// app/layout.tsx (No Provider needed!)
{children}

// Component
const selectedAgent = useAgentStore((state) => state.selectedAgent);
```

## Best Practices

### ✅ Do's
1. **Use selective subscriptions** for better performance
2. **Initialize stores on component mount** using initialization functions
3. **Validate data** before setting state (e.g., check if model is available)
4. **Use TypeScript** for type safety
5. **Partialize persistence** - only persist user selections, not derived/dynamic data
6. **Log actions** for debugging
7. **Handle errors** gracefully with error state

### ❌ Don'ts
1. **Don't subscribe to entire store** unless you need all fields
2. **Don't persist everything** - avoid stale data
3. **Don't call async actions in render** - use effects or event handlers
4. **Don't modify state directly** - always use `set()`
5. **Don't forget to initialize** - data won't load automatically

## Testing

### Unit Testing Stores
```typescript
import { useAgentStore } from '@/stores/agentStore';

describe('AgentStore', () => {
  beforeEach(() => {
    // Reset store before each test
    useAgentStore.getState().reset();
  });

  it('should set selected agent', () => {
    const { setSelectedAgent, selectedAgent } = useAgentStore.getState();
    
    setSelectedAgent('chat');
    expect(useAgentStore.getState().selectedAgent).toBe('chat');
  });

  it('should load agents', async () => {
    const { loadAgents, availableAgents } = useAgentStore.getState();
    
    await loadAgents();
    expect(useAgentStore.getState().availableAgents.length).toBeGreaterThan(0);
  });
});
```

### Component Testing
```typescript
import { render, screen } from '@testing-library/react';
import { useAgentStore } from '@/stores/agentStore';

it('renders with selected agent', () => {
  useAgentStore.setState({ selectedAgent: 'chat' });
  
  render(<AgentSelector />);
  expect(screen.getByText('Chat Agent')).toBeInTheDocument();
});
```

## Future Enhancements

### Potential Additions
1. **Canvas Store**: Migrate CanvasContext to Zustand
2. **Chat Store**: Centralize chat/thread state
3. **Zustand DevTools**: Add for enhanced debugging
4. **Immer Middleware**: Simplify nested state updates
5. **Computed State**: Add more derived state helpers

## References

- [Zustand Documentation](https://github.com/pmndrs/zustand)
- [Zustand Persist Middleware](https://docs.pmnd.rs/zustand/integrations/persisting-store-data)
- [TypeScript Guide](https://docs.pmnd.rs/zustand/guides/typescript)
- [Performance Optimization](https://docs.pmnd.rs/zustand/guides/performance)

## Related Documentation
- [AG-UI Integration](./ag-ui-integration.md)
- [Hooks Overview](./hooks/README.md)
- [Component Architecture](./components/README.md)

---

**Migration Completed**: December 26, 2025  
**Implementation Plan**: [011-migrate-to-zustand-state-management.md](../../1-implementation-plans/011-migrate-to-zustand-state-management.md)
