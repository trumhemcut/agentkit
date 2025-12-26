# Implementation Plan: Migrate to Zustand State Management

**Created**: December 26, 2025  
**Status**: Planning  
**Priority**: Medium  
**Estimated Time**: 2-3 hours

## Overview

Migrate from React Context to Zustand for global state management to improve:
- Performance (selective re-renders)
- Developer experience (less boilerplate, no Provider wrapping)
- Maintainability (cleaner API, easier testing)
- Scalability (better for growing app complexity)

## Goals

1. Replace `AgentSelectionContext` with Zustand store
2. Replace `useModelSelection` hook with Zustand store (bonus)
3. Maintain backward compatibility during migration
4. Improve performance with selective subscriptions
5. Simplify provider setup (remove Provider wrappers)

## Architecture Changes

### Before (Current)
```
app/layout.tsx
  └─ AgentSelectionProvider (Context)
       └─ CanvasProvider (Context)
            └─ Children
```

### After (Zustand)
```
app/layout.tsx
  └─ Children (no Providers needed!)

// Stores are global singletons
stores/agentStore.ts  - Agent selection state
stores/modelStore.ts  - Model selection state
```

## Dependencies

### Install Zustand

```bash
npm install zustand
# or
pnpm add zustand
```

**Version**: `^4.5.0` (latest stable)

**Bundle size**: ~3KB gzipped (much smaller than Context boilerplate)

## Implementation Steps

### Phase 1: Setup Zustand Infrastructure

#### Task 1.1: Create Agent Store
**File**: `frontend/stores/agentStore.ts`

**Implementation**:
- Create Zustand store with agent selection state
- Add persist middleware for localStorage sync
- Add async action to fetch available agents
- Add TypeScript types for store state

**Interface**:
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
- ✅ Persist `selectedAgent` to localStorage
- ✅ Auto-load agents on first access
- ✅ Validate agent selection against available agents
- ✅ Console logging for debugging
- ✅ Error handling

#### Task 1.2: Create Model Store
**File**: `frontend/stores/modelStore.ts`

**Implementation**:
- Create Zustand store with model selection state
- Add persist middleware
- Add async action to fetch available models

**Interface**:
```typescript
interface ModelStore {
  // State
  selectedModel: string;
  availableModels: LLMModel[];
  loading: boolean;
  error: string | null;
  
  // Actions
  setSelectedModel: (modelId: string) => void;
  loadModels: () => Promise<void>;
  reset: () => void;
}
```

### Phase 2: Migrate Components

#### Task 2.1: Update AgentSelector Component
**File**: `frontend/components/AgentSelector.tsx`

**Changes**:
- Replace `import { useAgentSelection } from '@/contexts/AgentSelectionContext'`
- With `import { useAgentStore } from '@/stores/agentStore'`
- Update hook usage to Zustand API
- Add selective subscription for better performance

**Before**:
```typescript
const { selectedAgent, availableAgents, setSelectedAgent, loading } = useAgentSelection();
```

**After**:
```typescript
const selectedAgent = useAgentStore((state) => state.selectedAgent);
const availableAgents = useAgentStore((state) => state.availableAgents);
const setSelectedAgent = useAgentStore((state) => state.setSelectedAgent);
const loading = useAgentStore((state) => state.loading);
```

**Or use shallow for multiple values**:
```typescript
const { selectedAgent, availableAgents, setSelectedAgent, loading } = useAgentStore();
```

#### Task 2.2: Update ChatContainer Component
**File**: `frontend/components/ChatContainer.tsx`

**Changes**:
- Replace Context import with store import
- Use selective subscription (only subscribe to `selectedAgent`)
- Remove unnecessary re-renders

**Optimization**:
```typescript
// Only re-render when selectedAgent changes
const selectedAgent = useAgentStore((state) => state.selectedAgent);
```

#### Task 2.3: Update ModelSelector Component
**File**: `frontend/components/ModelSelector.tsx`

**Changes**:
- Replace hook with store
- Use selective subscription

#### Task 2.4: Remove Provider Wrappers
**File**: `frontend/app/layout.tsx`

**Changes**:
- Remove `<AgentSelectionProvider>` wrapper
- Keep `<CanvasProvider>` (migrate later if needed)
- Clean up imports

**Before**:
```typescript
<AgentSelectionProvider>
  <CanvasProvider>
    {children}
  </CanvasProvider>
</AgentSelectionProvider>
```

**After**:
```typescript
<CanvasProvider>
  {children}
</CanvasProvider>
```

### Phase 3: Initialize Stores

#### Task 3.1: Add Store Initialization
**File**: `frontend/app/layout.tsx` or `frontend/lib/stores.ts`

**Implementation**:
- Create initialization function
- Call on app mount
- Handle errors gracefully

**Option A: Auto-initialize in store**:
```typescript
// In agentStore.ts - auto-load on first access
const useAgentStore = create<AgentStore>()((set, get) => ({
  selectedAgent: '',
  availableAgents: [],
  loading: false,
  
  // Auto-initialize
  _hasInitialized: false,
  _initialize: async () => {
    if (get()._hasInitialized) return;
    set({ _hasInitialized: true });
    await get().loadAgents();
  },
  
  // ... rest of store
}));

// In component - auto-load on first use
const selectedAgent = useAgentStore((state) => {
  state._initialize(); // Triggers load if not initialized
  return state.selectedAgent;
});
```

**Option B: Explicit initialization**:
```typescript
// In app/layout.tsx
'use client';

import { useEffect } from 'react';
import { useAgentStore } from '@/stores/agentStore';
import { useModelStore } from '@/stores/modelStore';

function StoreInitializer() {
  useEffect(() => {
    useAgentStore.getState().loadAgents();
    useModelStore.getState().loadModels();
  }, []);
  return null;
}

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        <StoreInitializer />
        {children}
      </body>
    </html>
  );
}
```

**Recommendation**: Use Option A (auto-initialize) for simpler API.

### Phase 4: Cleanup

#### Task 4.1: Remove Old Context Files
**Files to delete**:
- `frontend/contexts/AgentSelectionContext.tsx`
- `frontend/hooks/useAgentSelection.ts` (if not used elsewhere)
- `frontend/hooks/useModelSelection.ts` (if migrated)

**Alternative**: Keep as deprecated with redirect:
```typescript
// contexts/AgentSelectionContext.tsx (deprecated)
/**
 * @deprecated Use `import { useAgentStore } from '@/stores/agentStore'` instead
 */
export function useAgentSelection() {
  console.warn('useAgentSelection is deprecated. Use useAgentStore instead.');
  return useAgentStore();
}
```

#### Task 4.2: Update Documentation
**Files to update**:
- `.docs/2-knowledge-base/frontend/state-management.md` - Add Zustand section
- `.docs/2-knowledge-base/frontend/hooks/overview.md` - Update deprecation notices
- `README.md` - Update architecture diagram if present

### Phase 5: Testing

#### Task 5.1: Manual Testing
- [ ] Agent selection persists across page refreshes
- [ ] Agent changes reflect in both AgentSelector and ChatContainer
- [ ] Model selection works correctly
- [ ] No console errors or warnings
- [ ] localStorage keys are correct
- [ ] Initial load shows correct default agent/model

#### Task 5.2: Browser DevTools Check
- [ ] Check React DevTools - fewer re-renders
- [ ] Check localStorage - correct keys and values
- [ ] Check Network tab - agents/models fetched once
- [ ] Check Console - initialization logs correct

#### Task 5.3: Performance Verification
- [ ] Compare re-render count (Context vs Zustand)
- [ ] Check if only relevant components re-render on state change
- [ ] Verify no memory leaks (store cleanup)

## File Structure

### New Files
```
frontend/
├── stores/
│   ├── agentStore.ts       # Agent selection store (NEW)
│   └── modelStore.ts       # Model selection store (NEW)
```

### Modified Files
```
frontend/
├── app/
│   └── layout.tsx          # Remove Provider wrappers
├── components/
│   ├── AgentSelector.tsx   # Use store instead of context
│   ├── ChatContainer.tsx   # Use store with selective subscription
│   └── ModelSelector.tsx   # Use store instead of hook
```

### Deleted Files (Optional)
```
frontend/
├── contexts/
│   └── AgentSelectionContext.tsx  # Delete or deprecate
├── hooks/
│   ├── useAgentSelection.ts       # Delete or deprecate
│   └── useModelSelection.ts       # Delete or deprecate
```

## Migration Strategy

### Option 1: Big Bang Migration (Recommended for small app)
- Migrate everything at once
- Faster, cleaner
- Risk: More things to debug if issues arise

### Option 2: Gradual Migration
- Keep Context and Zustand side-by-side temporarily
- Migrate component by component
- Safer but more complex

**Recommendation**: Option 1 - app is small, migration is straightforward.

## Rollback Plan

If issues arise:

1. **Git revert** to previous commit
2. **Quick fix**: Keep Zustand but add Context wrapper that uses store:
```typescript
// Temporary compatibility layer
export function AgentSelectionProvider({ children }) {
  const store = useAgentStore();
  return (
    <AgentSelectionContext.Provider value={store}>
      {children}
    </AgentSelectionContext.Provider>
  );
}
```

## Code Examples

### Complete Agent Store Implementation

```typescript
// stores/agentStore.ts
import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { AgentMetadata } from '@/types/agent';
import { fetchAvailableAgents } from '@/services/api';

interface AgentStore {
  selectedAgent: string;
  availableAgents: AgentMetadata[];
  loading: boolean;
  error: string | null;
  
  setSelectedAgent: (agentId: string) => void;
  loadAgents: () => Promise<void>;
  reset: () => void;
}

export const useAgentStore = create<AgentStore>()(
  persist(
    (set, get) => ({
      // Initial state
      selectedAgent: '',
      availableAgents: [],
      loading: false,
      error: null,
      
      // Actions
      setSelectedAgent: (agentId: string) => {
        console.log('[AgentStore] Setting agent to:', agentId);
        set({ selectedAgent: agentId });
      },
      
      loadAgents: async () => {
        const { loading } = get();
        if (loading) return; // Prevent duplicate loads
        
        try {
          set({ loading: true, error: null });
          console.log('[AgentStore] Loading agents...');
          
          const response = await fetchAvailableAgents();
          
          // Get saved agent from store or use default
          const currentAgent = get().selectedAgent;
          const agentToSelect = currentAgent && 
            response.agents.some(a => a.id === currentAgent)
              ? currentAgent
              : response.default;
          
          set({
            availableAgents: response.agents,
            selectedAgent: agentToSelect,
            loading: false,
          });
          
          console.log('[AgentStore] Loaded agents:', response.agents.length);
        } catch (err) {
          console.error('[AgentStore] Failed to load agents:', err);
          set({
            error: err instanceof Error ? err.message : 'Failed to load agents',
            loading: false,
          });
        }
      },
      
      reset: () => {
        set({
          selectedAgent: '',
          availableAgents: [],
          loading: false,
          error: null,
        });
      },
    }),
    {
      name: 'agent-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({ selectedAgent: state.selectedAgent }),
    }
  )
);

// Auto-load agents on first access
let hasInitialized = false;
export const initializeAgentStore = () => {
  if (hasInitialized) return;
  hasInitialized = true;
  useAgentStore.getState().loadAgents();
};
```

### Usage in Components

```typescript
// components/AgentSelector.tsx
import { useAgentStore } from '@/stores/agentStore';
import { useEffect } from 'react';
import { initializeAgentStore } from '@/stores/agentStore';

export function AgentSelector() {
  // Auto-initialize on mount
  useEffect(() => {
    initializeAgentStore();
  }, []);
  
  // Selective subscriptions for better performance
  const selectedAgent = useAgentStore((state) => state.selectedAgent);
  const availableAgents = useAgentStore((state) => state.availableAgents);
  const loading = useAgentStore((state) => state.loading);
  const setSelectedAgent = useAgentStore((state) => state.setSelectedAgent);
  
  // ... rest of component
}

// components/ChatContainer.tsx
import { useAgentStore } from '@/stores/agentStore';

export function ChatContainer() {
  // Only subscribe to selectedAgent - won't re-render on other changes
  const selectedAgent = useAgentStore((state) => state.selectedAgent);
  
  const handleSendMessage = async (content: string) => {
    console.log('Sending with agent:', selectedAgent);
    await sendChatMessage(/*...*/, selectedAgent, /*...*/);
  };
  
  // ... rest of component
}
```

## Benefits After Migration

### Performance
- ✅ Fewer re-renders (selective subscriptions)
- ✅ No Provider re-render cascade
- ✅ Smaller bundle size vs Context boilerplate

### Developer Experience
- ✅ Less boilerplate (no Provider wrappers)
- ✅ Simpler API (direct store access)
- ✅ Better TypeScript inference
- ✅ Easier to test (just import store)

### Maintainability
- ✅ Clearer separation of concerns
- ✅ Easier to add new stores
- ✅ Better debugging (Zustand DevTools)
- ✅ Simpler async logic

## Timeline

1. **Phase 1**: Setup (30 min)
   - Install Zustand
   - Create stores

2. **Phase 2**: Migration (1 hour)
   - Update components
   - Remove Providers

3. **Phase 3**: Testing (30 min)
   - Manual testing
   - Performance check

4. **Phase 4**: Cleanup (30 min)
   - Remove old files
   - Update docs

**Total**: 2-3 hours

## Success Criteria

- [ ] No Context Providers in layout.tsx
- [ ] Agent selection syncs across all components
- [ ] State persists to localStorage correctly
- [ ] No console errors
- [ ] Performance improved (fewer re-renders)
- [ ] Documentation updated

## Questions to Consider

1. **Should we migrate CanvasContext too?**
   - Yes, for consistency (separate task)
   - No, it's working fine

2. **Keep old hooks for backward compatibility?**
   - Yes, with deprecation warnings
   - No, clean break

3. **Add Zustand DevTools?**
   - Yes, helpful for debugging
   - No, keep bundle small

## Next Steps

1. Review this plan with team
2. Create feature branch: `feature/zustand-migration`
3. Install dependencies
4. Implement Phase 1 (stores)
5. Test stores in isolation
6. Proceed with component migration

## References

- [Zustand Documentation](https://github.com/pmndrs/zustand)
- [Zustand Persist Middleware](https://docs.pmnd.rs/zustand/integrations/persisting-store-data)
- [React State Management Comparison](https://react.dev/learn/scaling-up-with-reducer-and-context#comparing-context-with-a-reducer)

---

**Note**: This plan focuses on agent/model selection. Canvas state management can be migrated in a separate task if needed.
