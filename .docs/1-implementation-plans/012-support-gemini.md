# Implementation Plan: Gemini Provider Support

**Requirement**: [012-support-gemini.md](../0-requirements/012-support-gemini.md)

**Summary**: Add Google Gemini as a new LLM provider alongside Ollama, allowing users to select between different providers and their respective models in the UI.

## Architecture Overview

This implementation adds Gemini as a new provider type in the multi-provider architecture:
- **Current**: Single Ollama provider with model selection
- **Target**: Multiple providers (Ollama, Gemini) with provider-specific models
- **UI Pattern**: Provider selection → Model selection (hierarchical)

## Implementation Breakdown

---

## 1. Backend Implementation

**Owner**: Backend Agent (see [backend.agent.md](../../.github/agents/backend.agent.md))

### Task 1.1: Create Gemini Provider Class

**File**: `backend/llm/gemini_provider.py` (new)

**Requirements**:
- Create `GeminiProvider` class following Ollama pattern
- Use `langchain-google-genai` library
- Support streaming responses
- Handle authentication via API key
- Default to `gemini-1.5-flash` model

**Implementation Pattern**:
```python
from langchain_google_genai import ChatGoogleGenerativeAI
from config import settings


class GeminiProvider:
    def __init__(self, model: str = None):
        """
        Initialize Gemini provider with optional model parameter
        
        Args:
            model: Model name (e.g., "gemini-1.5-flash", "gemini-1.5-pro")
                   Falls back to settings.GEMINI_MODEL if not provided
        """
        self.model = ChatGoogleGenerativeAI(
            model=model or settings.GEMINI_MODEL,
            google_api_key=settings.GEMINI_API_KEY,
            streaming=True
        )
    
    def get_model(self):
        return self.model
```

**Dependencies**:
- Add `langchain-google-genai` to `requirements.txt`
- Environment variable: `GEMINI_API_KEY`

---

### Task 1.2: Update Provider Factory

**File**: `backend/llm/provider_factory.py`

**Changes**:
```python
from llm.ollama_provider import OllamaProvider
from llm.gemini_provider import GeminiProvider


class LLMProviderFactory:
    @staticmethod
    def get_provider(provider_type: str = "ollama", model: str = None):
        """
        Get LLM provider instance
        
        Args:
            provider_type: Type of provider ("ollama", "gemini")
            model: Optional model name to use with the provider
        
        Returns:
            Provider instance
        """
        if provider_type == "ollama":
            return OllamaProvider(model=model)
        elif provider_type == "gemini":
            return GeminiProvider(model=model)
        raise ValueError(f"Unknown provider: {provider_type}")
```

---

### Task 1.3: Create Gemini Client for Model Listing

**File**: `backend/llm/gemini_client.py` (new)

**Requirements**:
- Query available Gemini models
- Return structured model list with metadata
- Handle authentication errors gracefully
- Follow pattern from `ollama_client.py`

**Implementation Pattern**:
```python
import httpx
from typing import Dict
from config import settings


class GeminiClient:
    """Client for interacting with Google AI API"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.timeout = 10.0
    
    async def list_available_models(self) -> Dict[str, any]:
        """
        Query Gemini API for available models
        Returns structured list of models with metadata
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/models?key={self.api_key}"
                )
                response.raise_for_status()
                data = response.json()
                
                # Parse and structure models
                models = []
                for model_info in data.get("models", []):
                    model_name = model_info.get("name", "").replace("models/", "")
                    
                    # Filter to text generation models only
                    if "generateContent" in model_info.get("supportedGenerationMethods", []):
                        display_name = model_name.replace("-", " ").title()
                        
                        models.append({
                            "id": model_name,
                            "name": display_name,
                            "size": "Google Cloud",  # No local size
                            "available": True,
                            "provider": "gemini"
                        })
                
                return {
                    "models": models,
                    "default": settings.GEMINI_MODEL
                }
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                return {
                    "models": [],
                    "default": settings.GEMINI_MODEL,
                    "error": "Invalid Gemini API key"
                }
            return {
                "models": [],
                "default": settings.GEMINI_MODEL,
                "error": f"Gemini API error: {str(e)}"
            }
        except Exception as e:
            return {
                "models": [],
                "default": settings.GEMINI_MODEL,
                "error": f"Error fetching Gemini models: {str(e)}"
            }
    
    async def check_model_available(self, model_name: str) -> bool:
        """Check if a specific Gemini model is available"""
        models_data = await self.list_available_models()
        return any(m["id"] == model_name for m in models_data.get("models", []))


# Global client instance
gemini_client = GeminiClient()
```

---

### Task 1.4: Update Configuration

**File**: `backend/config.py`

**Changes**:
```python
class Settings(BaseSettings):
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    
    # LLM settings - Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen:7b"
    
    # LLM settings - Gemini
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"
    
    # Default provider
    DEFAULT_PROVIDER: str = "ollama"
    DEFAULT_MODEL: str = "qwen:7b"
    
    # CORS settings
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    # Agent settings
    DEFAULT_AGENT: str = "chat"
    
    class Config:
        env_file = ".env"
```

**Environment Variables** (`.env.example`):
```bash
# LLM Provider Settings
DEFAULT_PROVIDER=ollama
DEFAULT_MODEL=qwen:7b

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen:7b

# Gemini Configuration
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-1.5-flash
```

---

### Task 1.5: Create Unified Provider Client

**File**: `backend/llm/provider_client.py` (new)

**Requirements**:
- Aggregate models from all providers
- Return unified structure for frontend
- Handle provider-specific errors
- Support provider filtering

**Implementation**:
```python
from typing import Dict, List, Optional
from llm.ollama_client import ollama_client
from llm.gemini_client import gemini_client
from config import settings


class ProviderClient:
    """Unified client for all LLM providers"""
    
    async def list_all_models(self, provider_filter: Optional[str] = None) -> Dict:
        """
        List models from all providers or specific provider
        
        Args:
            provider_filter: Optional provider name to filter by ("ollama", "gemini")
        
        Returns:
            Dict with providers, models, and defaults
        """
        providers = []
        all_models = []
        errors = []
        
        # Fetch Ollama models
        if not provider_filter or provider_filter == "ollama":
            ollama_data = await ollama_client.list_available_models()
            if "error" in ollama_data:
                errors.append({"provider": "ollama", "error": ollama_data["error"]})
            else:
                for model in ollama_data.get("models", []):
                    model["provider"] = "ollama"
                    all_models.append(model)
                
                providers.append({
                    "id": "ollama",
                    "name": "Ollama",
                    "available": len(ollama_data.get("models", [])) > 0
                })
        
        # Fetch Gemini models
        if not provider_filter or provider_filter == "gemini":
            gemini_data = await gemini_client.list_available_models()
            if "error" in gemini_data:
                errors.append({"provider": "gemini", "error": gemini_data["error"]})
            else:
                for model in gemini_data.get("models", []):
                    model["provider"] = "gemini"
                    all_models.append(model)
                
                providers.append({
                    "id": "gemini",
                    "name": "Gemini",
                    "available": len(gemini_data.get("models", [])) > 0
                })
        
        return {
            "providers": providers,
            "models": all_models,
            "default_provider": settings.DEFAULT_PROVIDER,
            "default_model": settings.DEFAULT_MODEL,
            "errors": errors if errors else None
        }
    
    async def get_models_by_provider(self, provider: str) -> List[Dict]:
        """Get models for a specific provider"""
        data = await self.list_all_models(provider_filter=provider)
        return data.get("models", [])


# Global instance
provider_client = ProviderClient()
```

---

### Task 1.6: Update API Routes

**File**: `backend/api/routes.py`

**Changes**:
1. Update `/models` endpoint to return all providers:

```python
from llm.provider_client import provider_client

@router.get("/models")
async def list_models():
    """List available models from all providers"""
    try:
        models_data = await provider_client.list_all_models()
        return models_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching models: {str(e)}")


@router.get("/models/{provider}")
async def list_provider_models(provider: str):
    """List models from a specific provider"""
    try:
        models = await provider_client.get_models_by_provider(provider)
        return {"models": models}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching models: {str(e)}")
```

---

### Task 1.7: Update Agent Base Class

**File**: `backend/agents/base_agent.py`

**Changes**: Update to accept provider parameter:

```python
def __init__(self, model: str = None, provider: str = None):
    """
    Initialize agent with optional model and provider
    
    Args:
        model: Optional model name
        provider: Optional provider type ("ollama", "gemini")
    """
    self.provider_type = provider or settings.DEFAULT_PROVIDER
    self.model_name = model or settings.DEFAULT_MODEL
    
    # Get appropriate provider
    provider_instance = LLMProviderFactory.get_provider(
        provider_type=self.provider_type,
        model=self.model_name
    )
    self.llm = provider_instance.get_model()
```

---

### Task 1.8: Update API Request Models

**File**: `backend/api/models.py`

**Changes**: Add provider field to request models:

```python
class RunAgentInput(BaseModel):
    thread_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    messages: List[Message]
    model: Optional[str] = None  # Model selection
    provider: Optional[str] = None  # Provider selection (new)
    agent: Optional[str] = "chat"
    
    # Canvas-specific optional fields
    artifact: Optional['Artifact'] = None
    artifact_id: Optional[str] = None
    selectedText: Optional['SelectedText'] = None
    action: Optional[Literal["create", "update", "partial_update", "chat"]] = None
```

---

### Task 1.9: Update Chat Endpoints

**File**: `backend/api/routes.py`

**Changes**: Pass provider to agent initialization:

```python
# In chat_endpoint function
if agent_id == "chat":
    from agents.chat_agent import ChatAgent
    # ... state preparation ...
    chat_agent = ChatAgent(
        model=input_data.model,
        provider=input_data.provider  # Pass provider
    )
    async for event in chat_agent.run(state):
        yield encoder.encode(event)

elif agent_id == "canvas":
    from agents.canvas_agent import CanvasAgent
    # ... state preparation ...
    canvas_agent = CanvasAgent(
        model=input_data.model,
        provider=input_data.provider  # Pass provider
    )
    # ... rest of canvas logic ...
```

---

## 2. Protocol (AG-UI)

**Communication contract between backend and frontend**

### Provider-Model Response Format

**Endpoint**: `GET /models`

**Response Structure**:
```typescript
{
  "providers": [
    {
      "id": "ollama",
      "name": "Ollama",
      "available": true
    },
    {
      "id": "gemini",
      "name": "Gemini",
      "available": true
    }
  ],
  "models": [
    {
      "id": "qwen:7b",
      "name": "Qwen 7B",
      "size": "7B parameters",
      "available": true,
      "provider": "ollama"
    },
    {
      "id": "gemini-1.5-flash",
      "name": "Gemini 1.5 Flash",
      "size": "Google Cloud",
      "available": true,
      "provider": "gemini"
    }
  ],
  "default_provider": "ollama",
  "default_model": "qwen:7b",
  "errors": null
}
```

### Chat Request Format

**Endpoint**: `POST /chat/{agent_id}`

**Request Body**:
```typescript
{
  "thread_id": "uuid",
  "run_id": "uuid",
  "messages": [...],
  "provider": "gemini",  // NEW: Provider selection
  "model": "gemini-1.5-flash",  // Model selection
  "agent": "chat"
}
```

---

## 3. Frontend Implementation

**Owner**: Frontend Agent (see [frontend.agent.md](../../.github/agents/frontend.agent.md))

### Task 3.1: Update TypeScript Types

**File**: `frontend/types/chat.ts`

**Changes**:
```typescript
export interface LLMProvider {
  id: string;
  name: string;
  available: boolean;
}

export interface LLMModel {
  id: string;
  name: string;
  size: string;
  available: boolean;
  provider: string;  // NEW: Provider association
}

export interface ModelsResponse {
  providers: LLMProvider[];  // NEW: Provider list
  models: LLMModel[];
  default_provider: string;  // NEW: Default provider
  default_model: string;
  errors?: Array<{ provider: string; error: string }>;
}

export interface ChatRequest {
  thread_id: string;
  run_id: string;
  messages: Message[];
  provider?: string;  // NEW: Provider selection
  model?: string;
  agent?: string;
}
```

---

### Task 3.2: Update Model Store (Zustand)

**File**: `frontend/stores/modelStore.ts`

**Changes**: Add provider state and selection:

```typescript
interface ModelStore {
  // State
  selectedProvider: string | null;  // NEW
  selectedModel: string | null;
  availableProviders: LLMProvider[];  // NEW
  availableModels: LLMModel[];
  loading: boolean;
  error: string | null;
  
  // Actions
  setSelectedProvider: (providerId: string) => void;  // NEW
  setSelectedModel: (modelId: string) => void;
  getProviderModels: (providerId: string) => LLMModel[];  // NEW
  loadModels: () => Promise<void>;
  getSelectedModelInfo: () => LLMModel | null;
  reset: () => void;
}

export const useModelStore = create<ModelStore>()(
  persist(
    (set, get) => ({
      // Initial state
      selectedProvider: null,
      selectedModel: null,
      availableProviders: [],
      availableModels: [],
      loading: false,
      error: null,
      
      // Set provider and auto-select first model
      setSelectedProvider: (providerId: string) => {
        const { availableProviders } = get();
        const provider = availableProviders.find(p => p.id === providerId);
        
        if (!provider || !provider.available) {
          console.error('[ModelStore] Provider not available:', providerId);
          return;
        }
        
        console.log('[ModelStore] Setting provider to:', providerId);
        
        // Get models for this provider
        const providerModels = get().getProviderModels(providerId);
        
        // Auto-select first available model
        const firstModel = providerModels.find(m => m.available);
        
        set({ 
          selectedProvider: providerId,
          selectedModel: firstModel?.id || null
        });
      },
      
      // Get models filtered by provider
      getProviderModels: (providerId: string) => {
        const { availableModels } = get();
        return availableModels.filter(m => m.provider === providerId);
      },
      
      loadModels: async () => {
        // ... existing load logic ...
        const response: ModelsResponse = await fetchAvailableModels();
        
        // Determine provider and model selection
        const currentProvider = get().selectedProvider;
        const currentModel = get().selectedModel;
        
        let finalProvider = currentProvider || response.default_provider;
        let finalModel = currentModel || response.default_model;
        
        // Validate provider exists
        const providerExists = response.providers.find(
          p => p.id === finalProvider && p.available
        );
        
        if (!providerExists) {
          // Fall back to first available provider
          const firstProvider = response.providers.find(p => p.available);
          finalProvider = firstProvider?.id || response.default_provider;
        }
        
        // Validate model exists and belongs to selected provider
        const modelExists = response.models.find(
          m => m.id === finalModel && 
               m.provider === finalProvider && 
               m.available
        );
        
        if (!modelExists) {
          // Fall back to first model of selected provider
          const providerModels = response.models.filter(
            m => m.provider === finalProvider && m.available
          );
          finalModel = providerModels[0]?.id || response.default_model;
        }
        
        set({
          availableProviders: response.providers,
          availableModels: response.models,
          selectedProvider: finalProvider,
          selectedModel: finalModel,
          loading: false,
        });
      },
      
      // ... rest of existing methods ...
    }),
    {
      name: MODEL_STORAGE_KEY,
      // Persist both provider and model
      partialize: (state) => ({ 
        selectedProvider: state.selectedProvider,
        selectedModel: state.selectedModel 
      }),
    }
  )
);
```

---

### Task 3.3: Create Provider Selector Component

**File**: `frontend/components/ProviderSelector.tsx` (new)

**Requirements**:
- Dropdown for provider selection
- Display provider availability status
- Shadcn UI DropdownMenu component
- Auto-load models when provider changes

**Implementation Pattern**:
```tsx
"use client";

import React from 'react';
import { Cloud, Server, Check, ChevronDown } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Button } from '@/components/ui/button';
import { useModelStore } from '@/stores/modelStore';
import { cn } from '@/lib/utils';

const providerIcons = {
  ollama: Server,
  gemini: Cloud,
};

export function ProviderSelector() {
  const selectedProvider = useModelStore((state) => state.selectedProvider);
  const availableProviders = useModelStore((state) => state.availableProviders);
  const setSelectedProvider = useModelStore((state) => state.setSelectedProvider);
  const loading = useModelStore((state) => state.loading);
  
  const currentProvider = availableProviders.find(p => p.id === selectedProvider);
  const Icon = currentProvider ? providerIcons[currentProvider.id] : Server;
  
  if (loading) {
    return <Button variant="ghost" size="sm" disabled>Loading...</Button>;
  }
  
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="sm" className="gap-2">
          <Icon className="h-4 w-4" />
          <span className="hidden sm:inline">
            {currentProvider?.name || 'Select Provider'}
          </span>
          <ChevronDown className="h-4 w-4" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-[200px]">
        <DropdownMenuLabel>Select Provider</DropdownMenuLabel>
        <DropdownMenuSeparator />
        {availableProviders.map((provider) => {
          const ProviderIcon = providerIcons[provider.id] || Server;
          return (
            <DropdownMenuItem
              key={provider.id}
              onClick={() => setSelectedProvider(provider.id)}
              disabled={!provider.available}
              className={cn(
                "flex items-center gap-2 cursor-pointer",
                !provider.available && "opacity-50 cursor-not-allowed"
              )}
            >
              <div className="flex h-5 w-5 items-center justify-center">
                {selectedProvider === provider.id && (
                  <Check className="h-4 w-4" />
                )}
              </div>
              <ProviderIcon className="h-4 w-4" />
              <span>{provider.name}</span>
            </DropdownMenuItem>
          );
        })}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
```

---

### Task 3.4: Update Model Selector Component

**File**: `frontend/components/ModelSelector.tsx`

**Changes**: Filter models by selected provider:

```tsx
export function ModelSelector() {
  const selectedProvider = useModelStore((state) => state.selectedProvider);
  const selectedModel = useModelStore((state) => state.selectedModel);
  const getProviderModels = useModelStore((state) => state.getProviderModels);
  const setSelectedModel = useModelStore((state) => state.setSelectedModel);
  const loading = useModelStore((state) => state.loading);
  const error = useModelStore((state) => state.error);
  
  // Filter models by selected provider
  const availableModels = selectedProvider 
    ? getProviderModels(selectedProvider)
    : [];
  
  // ... rest of component logic (same as before) ...
  // Just use filtered availableModels instead of all models
}
```

---

### Task 3.5: Update Header Component

**File**: `frontend/components/Header.tsx`

**Changes**: Add provider selector before model selector:

```tsx
import { ProviderSelector } from './ProviderSelector';
import { ModelSelector } from './ModelSelector';

export function Header() {
  return (
    <header className="border-b">
      <div className="flex items-center justify-between p-4">
        <div className="flex items-center gap-4">
          {/* ... existing elements ... */}
        </div>
        
        <div className="flex items-center gap-2">
          {/* Provider selector */}
          <ProviderSelector />
          
          {/* Model selector (filtered by provider) */}
          <ModelSelector />
        </div>
      </div>
    </header>
  );
}
```

---

### Task 3.6: Update API Client

**File**: `frontend/services/api.ts`

**Changes**: Include provider in chat requests:

```typescript
export async function sendChatMessage(
  agentId: string,
  request: ChatRequest
): Promise<ReadableStream> {
  const response = await fetch(`${API_BASE_URL}/chat/${agentId}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'text/event-stream',
    },
    body: JSON.stringify({
      ...request,
      provider: request.provider,  // Include provider
      model: request.model,
    }),
  });
  
  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }
  
  return response.body!;
}
```

---

### Task 3.7: Update Chat Hook

**File**: `frontend/hooks/useAgentSelection.ts` or similar

**Changes**: Pass provider from store to API:

```typescript
const sendMessage = async (content: string) => {
  const selectedProvider = useModelStore.getState().selectedProvider;
  const selectedModel = useModelStore.getState().selectedModel;
  
  const request: ChatRequest = {
    thread_id: threadId,
    run_id: generateRunId(),
    messages: [...],
    provider: selectedProvider,  // Include provider
    model: selectedModel,
    agent: agentId,
  };
  
  await sendChatMessage(agentId, request);
};
```

---

## 4. Testing & Validation

### Backend Tests

1. **Provider Tests** (`backend/tests/test_gemini_provider.py`):
   - Test Gemini provider initialization
   - Test authentication errors
   - Test model listing
   - Test streaming responses

2. **Provider Client Tests** (`backend/tests/test_provider_client.py`):
   - Test multi-provider aggregation
   - Test provider filtering
   - Test error handling

3. **API Tests** (`backend/tests/test_models_endpoint.py`):
   - Test `/models` endpoint with both providers
   - Test `/models/{provider}` endpoint
   - Test chat endpoint with provider parameter

### Frontend Tests

1. **Component Tests**:
   - ProviderSelector component rendering
   - ModelSelector filtering by provider
   - State management in Zustand store

2. **Integration Tests**:
   - Provider selection flow
   - Model selection after provider change
   - API request includes provider parameter

### Manual Testing

1. **Setup Gemini**:
   - Add `GEMINI_API_KEY` to `.env`
   - Verify API key validity
   - Check models appear in UI

2. **Provider Switching**:
   - Switch between Ollama and Gemini
   - Verify model list updates
   - Verify chat uses correct provider

3. **Error Handling**:
   - Test with invalid API key
   - Test with Ollama offline
   - Test with no providers available

---

## 5. Dependencies & Order

### Phase 1: Backend Foundation
1. Task 1.1: Create Gemini Provider ✓
2. Task 1.3: Create Gemini Client ✓
3. Task 1.4: Update Configuration ✓
4. Task 1.2: Update Provider Factory ✓

### Phase 2: Backend Integration
5. Task 1.5: Create Unified Provider Client ✓
6. Task 1.6: Update API Routes ✓
7. Task 1.8: Update API Request Models ✓
8. Task 1.7: Update Agent Base Class ✓
9. Task 1.9: Update Chat Endpoints ✓

### Phase 3: Frontend Foundation
10. Task 3.1: Update TypeScript Types ✓
11. Task 3.2: Update Model Store ✓

### Phase 4: Frontend Components
12. Task 3.3: Create Provider Selector ✓
13. Task 3.4: Update Model Selector ✓
14. Task 3.5: Update Header Component ✓

### Phase 5: Frontend Integration
15. Task 3.6: Update API Client ✓
16. Task 3.7: Update Chat Hook ✓

### Phase 6: Testing
17. Backend tests ✓
18. Frontend tests ✓
19. Integration testing ✓

---

## 6. Documentation Updates

### Files to Update:
1. `README.md`: Add Gemini setup instructions
2. `.env.example`: Add Gemini configuration
3. `backend/README.md`: Document provider system
4. `frontend/README.md`: Document provider UI components

### New Documentation:
1. `.docs/2-knowledge-base/llm-providers.md`: Provider architecture
2. `.docs/2-knowledge-base/gemini-integration.md`: Gemini-specific details

---

## 7. Rollout Considerations

### Backward Compatibility
- Existing installations default to Ollama
- Missing `GEMINI_API_KEY` gracefully disables Gemini
- Frontend handles partial provider availability

### Configuration Migration
- No breaking changes to existing config
- New environment variables are optional
- Default behavior unchanged (Ollama + qwen:7b)

### Error Handling
- Provider unavailability doesn't break app
- Clear error messages for API key issues
- Fallback to available providers

---

## 8. Future Enhancements

After initial implementation, consider:

1. **Additional Providers**: OpenAI, Anthropic, Azure OpenAI
2. **Provider-Specific Features**: Context windows, token limits
3. **Cost Tracking**: API usage monitoring
4. **Provider Health**: Connection status indicators
5. **Advanced Routing**: Auto-select provider based on task type

---

## Summary

This implementation adds Gemini as a new provider with a hierarchical provider→model selection UI. The architecture is extensible for future providers while maintaining backward compatibility with existing Ollama installations.

**Key Principles**:
- Provider-agnostic architecture
- Graceful degradation
- Clear separation between backend and frontend
- Extensible for future providers
- Maintains existing patterns

**Estimated Effort**:
- Backend: 4-6 hours
- Frontend: 3-4 hours
- Testing: 2-3 hours
- **Total**: 9-13 hours
