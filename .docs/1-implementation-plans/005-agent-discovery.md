# Implementation Plan: Agent Discovery System

**Requirement**: System will have multiple agents (ChatAgent, CanvasAgent, future agents). Backend should provide API to discover available agents. Frontend should allow users to select agents for chat.

**Related Files**:
- Backend: `backend/agents/`, `backend/api/routes.py`, `backend/config.py`
- Frontend: `frontend/components/`, `frontend/services/api.ts`, `frontend/types/agent.ts`

---

## 1. Backend Tasks (LangGraph + AG-UI)

**Delegate to Backend Agent** - See [.github/agents/backend.agent.md](.github/agents/backend.agent.md)

### Task 1.1: Create Agent Registry System
**File**: `backend/agents/agent_registry.py` (new)

Create a centralized registry for managing available agents:

```python
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class AgentMetadata:
    """Metadata describing an agent"""
    id: str  # Unique identifier (e.g., "chat", "canvas")
    name: str  # Display name (e.g., "Chat Agent", "Canvas Agent")
    description: str  # Brief description of agent capabilities
    icon: str  # Icon identifier for frontend
    available: bool  # Whether agent is currently available
    sub_agents: List[str]  # List of sub-agent IDs in graph
    features: List[str]  # List of feature tags


class AgentRegistry:
    """Registry for managing available agents"""
    
    def __init__(self):
        self._agents: Dict[str, AgentMetadata] = {}
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Initialize default agents"""
        # Register ChatAgent
        self.register_agent(AgentMetadata(
            id="chat",
            name="Chat Agent",
            description="General purpose conversational agent",
            icon="message-circle",
            available=True,
            sub_agents=[],
            features=["conversation", "streaming"]
        ))
        
        # Register CanvasAgent
        self.register_agent(AgentMetadata(
            id="canvas",
            name="Canvas Agent",
            description="Multi-agent system with artifact generation and editing",
            icon="layout",
            available=True,
            sub_agents=["generator", "editor"],
            features=["artifacts", "code-generation", "multi-step"]
        ))
    
    def register_agent(self, metadata: AgentMetadata):
        """Register a new agent"""
        self._agents[metadata.id] = metadata
    
    def get_agent(self, agent_id: str) -> Optional[AgentMetadata]:
        """Get agent metadata by ID"""
        return self._agents.get(agent_id)
    
    def list_agents(self, available_only: bool = True) -> List[AgentMetadata]:
        """List all registered agents"""
        agents = list(self._agents.values())
        if available_only:
            agents = [a for a in agents if a.available]
        return agents
    
    def is_available(self, agent_id: str) -> bool:
        """Check if agent is available"""
        agent = self.get_agent(agent_id)
        return agent.available if agent else False


# Global registry instance
agent_registry = AgentRegistry()
```

**Requirements**:
- Provide singleton registry accessible across backend
- Store agent metadata (id, name, description, features)
- Support dynamic agent registration for future extensibility
- Track sub-agents within each graph
- Include availability status

### Task 1.2: Create Agent Discovery API Endpoint
**File**: `backend/api/routes.py`

Add new endpoint to list available agents:

```python
@router.get("/agents")
async def list_agents():
    """List available agents with metadata"""
    from agents.agent_registry import agent_registry
    
    try:
        agents = agent_registry.list_agents(available_only=True)
        
        return {
            "agents": [
                {
                    "id": agent.id,
                    "name": agent.name,
                    "description": agent.description,
                    "icon": agent.icon,
                    "sub_agents": agent.sub_agents,
                    "features": agent.features
                }
                for agent in agents
            ],
            "default": "chat"  # Default agent selection
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error fetching agents: {str(e)}"
        )
```

**Requirements**:
- Return list of available agents with metadata
- Include default agent for initial selection
- Handle errors gracefully
- Filter out unavailable agents

**Response Schema**:
```json
{
  "agents": [
    {
      "id": "chat",
      "name": "Chat Agent",
      "description": "General purpose conversational agent",
      "icon": "message-circle",
      "sub_agents": [],
      "features": ["conversation", "streaming"]
    },
    {
      "id": "canvas",
      "name": "Canvas Agent", 
      "description": "Multi-agent system with artifact generation and editing",
      "icon": "layout",
      "sub_agents": ["generator", "editor"],
      "features": ["artifacts", "code-generation", "multi-step"]
    }
  ],
  "default": "chat"
}
```

### Task 1.3: Update Existing Endpoints to Accept Agent Parameter
**Files**: `backend/api/models.py`, `backend/api/routes.py`

Update request models to include agent selection:

```python
class RunAgentInput(BaseModel):
    thread_id: str
    run_id: str
    messages: List[MessageInput]
    model: Optional[str] = None
    agent: Optional[str] = "chat"  # Add agent selection

class CanvasMessageRequest(BaseModel):
    thread_id: str
    run_id: str
    messages: List[MessageInput]
    artifact: Optional[ArtifactV3] = None
    selectedText: Optional[SelectedText] = None
    action: Optional[str] = None
    model: Optional[str] = None
    agent: Optional[str] = "canvas"  # Add agent selection
```

Update route logic to dynamically select graph based on agent parameter:

```python
@router.post("/chat")
async def chat_endpoint(input_data: RunAgentInput, request: Request):
    """AG-UI compliant chat endpoint with agent selection"""
    from agents.agent_registry import agent_registry
    
    # Validate agent exists and is available
    if not agent_registry.is_available(input_data.agent):
        raise HTTPException(
            status_code=400,
            detail=f"Agent '{input_data.agent}' not available"
        )
    
    # Select appropriate graph based on agent
    if input_data.agent == "chat":
        graph = create_chat_graph(model=input_data.model)
    elif input_data.agent == "canvas":
        graph = create_canvas_graph(model=input_data.model)
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown agent: {input_data.agent}"
        )
    
    # Continue with existing logic...
```

**Requirements**:
- Add `agent` field to request schemas with default values
- Validate agent ID against registry
- Dynamically route to appropriate graph based on agent selection
- Return meaningful errors for invalid agents

### Task 1.4: Update Configuration for Default Agent
**File**: `backend/config.py`

Add configuration for default agent:

```python
class Settings(BaseSettings):
    # Existing settings...
    
    # Agent settings
    DEFAULT_AGENT: str = "chat"
    
    class Config:
        env_file = ".env"
```

**Requirements**:
- Add DEFAULT_AGENT configuration
- Allow override via environment variable
- Use in API endpoints as fallback

---

## 2. Protocol (AG-UI)

**Define communication contract between backend and frontend:**

### Agent Discovery Protocol

**Endpoint**: `GET /api/agents`

**Response Format**:
```typescript
interface AgentMetadata {
  id: string;           // Unique agent identifier
  name: string;         // Display name
  description: string;  // Brief description
  icon: string;         // Icon identifier
  sub_agents: string[]; // List of sub-agent IDs
  features: string[];   // Feature tags
}

interface AgentsResponse {
  agents: AgentMetadata[];
  default: string;      // Default agent ID
}
```

### Agent Selection Protocol

**Request Format**:
All existing endpoints (`/chat`, `/canvas`) accept optional `agent` parameter:

```typescript
interface ChatRequest {
  thread_id: string;
  run_id: string;
  messages: Message[];
  model?: string;
  agent?: string;  // Agent selection
}
```

**Error Handling**:
- Invalid agent ID → HTTP 400 with error message
- Unavailable agent → HTTP 400 with error message
- Missing agent → Use default from config

---

## 3. Frontend Tasks (AG-UI + React)

**Delegate to Frontend Agent** - See [.github/agents/frontend.agent.md](.github/agents/frontend.agent.md)

### Task 3.1: Create Agent Types
**File**: `frontend/types/agent.ts`

Define TypeScript interfaces for agents:

```typescript
/**
 * Agent metadata from backend
 */
export interface AgentMetadata {
  id: string;
  name: string;
  description: string;
  icon: string;
  sub_agents: string[];
  features: string[];
}

/**
 * Response from /api/agents endpoint
 */
export interface AgentsResponse {
  agents: AgentMetadata[];
  default: string;
}

/**
 * Agent selection state
 */
export interface AgentSelection {
  selectedAgent: string;
  availableAgents: AgentMetadata[];
}
```

### Task 3.2: Add Agent API Client Function
**File**: `frontend/services/api.ts`

Add function to fetch available agents:

```typescript
/**
 * Fetch available agents from backend
 * 
 * @returns AgentsResponse with list of agents and default
 */
export async function fetchAvailableAgents(): Promise<AgentsResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/agents`);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch agents: ${response.statusText}`);
    }
    
    const data: AgentsResponse = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching agents:', error);
    throw error;
  }
}
```

Update existing chat functions to include agent parameter:

```typescript
export async function sendChatMessage(
  messages: Message[],
  threadId: string,
  runId: string,
  model: string | undefined,
  agent: string | undefined,  // Add agent parameter
  onEvent: (event: any) => void
): Promise<void> {
  // Update request body to include agent
  const requestBody: ChatRequest = {
    thread_id: threadId,
    run_id: runId,
    messages,
    model,
    agent
  };
  
  // Continue with existing logic...
}
```

### Task 3.3: Create Agent Selector Component
**File**: `frontend/components/AgentSelector.tsx` (new)

Create Shadcn UI component for agent selection:

```typescript
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { useAgentSelection } from '@/hooks/useAgentSelection';
import { MessageCircle, Layout } from 'lucide-react';

/**
 * Agent selector component
 * 
 * Dropdown to select active agent for chat
 * Positioned in header similar to ChatGPT UI
 */
export function AgentSelector() {
  const { selectedAgent, availableAgents, setSelectedAgent } = useAgentSelection();
  
  // Map icon names to lucide icons
  const getIcon = (iconName: string) => {
    switch (iconName) {
      case 'message-circle':
        return <MessageCircle className="h-4 w-4 mr-2" />;
      case 'layout':
        return <Layout className="h-4 w-4 mr-2" />;
      default:
        return <MessageCircle className="h-4 w-4 mr-2" />;
    }
  };
  
  const currentAgent = availableAgents.find(a => a.id === selectedAgent);
  
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" className="min-w-[180px] justify-start">
          {currentAgent && (
            <>
              {getIcon(currentAgent.icon)}
              <span>{currentAgent.name}</span>
            </>
          )}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-[280px]">
        {availableAgents.map((agent) => (
          <DropdownMenuItem
            key={agent.id}
            onClick={() => setSelectedAgent(agent.id)}
            className="flex flex-col items-start gap-1"
          >
            <div className="flex items-center">
              {getIcon(agent.icon)}
              <span className="font-medium">{agent.name}</span>
            </div>
            <span className="text-sm text-muted-foreground pl-6">
              {agent.description}
            </span>
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
```

**Requirements**:
- Use Shadcn UI DropdownMenu component
- Display agent name and icon in trigger
- Show agent description in dropdown items
- Highlight currently selected agent
- Update selection in global state
- Position in header alongside ModelSelector

### Task 3.4: Create Agent Selection Hook
**File**: `frontend/hooks/useAgentSelection.ts` (new)

Create hook to manage agent selection state:

```typescript
import { useState, useEffect } from 'react';
import { AgentMetadata } from '@/types/agent';
import { fetchAvailableAgents } from '@/services/api';

const AGENT_STORAGE_KEY = 'selected_agent';

/**
 * Hook for managing agent selection
 * 
 * Fetches available agents from backend and manages selection state
 * Persists selection to localStorage
 */
export function useAgentSelection() {
  const [selectedAgent, setSelectedAgentState] = useState<string>('chat');
  const [availableAgents, setAvailableAgents] = useState<AgentMetadata[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Fetch available agents on mount
  useEffect(() => {
    const loadAgents = async () => {
      try {
        setLoading(true);
        const response = await fetchAvailableAgents();
        setAvailableAgents(response.agents);
        
        // Load saved selection or use default
        const saved = localStorage.getItem(AGENT_STORAGE_KEY);
        const initial = saved || response.default;
        
        // Validate saved agent is still available
        const isValid = response.agents.some(a => a.id === initial);
        setSelectedAgentState(isValid ? initial : response.default);
        
        setError(null);
      } catch (err) {
        console.error('Failed to load agents:', err);
        setError('Failed to load agents');
        
        // Fallback to default
        setAvailableAgents([]);
        setSelectedAgentState('chat');
      } finally {
        setLoading(false);
      }
    };
    
    loadAgents();
  }, []);
  
  // Persist selection to localStorage
  const setSelectedAgent = (agentId: string) => {
    setSelectedAgentState(agentId);
    localStorage.setItem(AGENT_STORAGE_KEY, agentId);
  };
  
  return {
    selectedAgent,
    availableAgents,
    setSelectedAgent,
    loading,
    error
  };
}
```

**Requirements**:
- Fetch agents from backend on mount
- Persist selection to localStorage
- Validate stored selection is still available
- Provide loading and error states
- Export selection state for use in other components

### Task 3.5: Update Header Component
**File**: `frontend/components/Header.tsx`

Add AgentSelector alongside ModelSelector:

```typescript
import { ModelSelector } from './ModelSelector';
import { AgentSelector } from './AgentSelector';

/**
 * Header component
 * 
 * Application header with agent and model selectors
 */
export function Header() {
  return (
    <header className="bg-background shadow-sm">
      <div className="flex h-16 items-center px-6 justify-start gap-4">
        <AgentSelector />
        <ModelSelector />
      </div>
    </header>
  );
}
```

**Requirements**:
- Position AgentSelector before ModelSelector
- Maintain consistent spacing with gap-4
- Ensure responsive layout

### Task 3.6: Update Chat Hooks to Use Selected Agent
**Files**: `frontend/hooks/useMessages.ts`, `frontend/hooks/useCanvasChat.ts`

Update hooks to include agent parameter in API calls:

```typescript
// In useMessages.ts
import { useAgentSelection } from './useAgentSelection';

export function useMessages() {
  const { selectedAgent } = useAgentSelection();
  
  // When calling sendChatMessage
  await sendChatMessage(
    messages,
    currentThread.thread_id,
    runId,
    selectedModel,
    selectedAgent,  // Pass selected agent
    handleEvent
  );
}

// In useCanvasChat.ts
import { useAgentSelection } from './useAgentSelection';

export function useCanvasChat() {
  const { selectedAgent } = useAgentSelection();
  
  // When calling sendCanvasMessage
  await sendCanvasMessage(
    messages,
    currentThread.thread_id,
    runId,
    selectedModel,
    artifact,
    selectedText,
    action,
    selectedAgent,  // Pass selected agent
    handleEvent
  );
}
```

**Requirements**:
- Import and use useAgentSelection hook
- Pass selectedAgent to API calls
- Ensure agent selection is reactive

### Task 3.7: Update Chat Request Types
**File**: `frontend/types/chat.ts`

Update ChatRequest interface:

```typescript
export interface ChatRequest {
  thread_id: string;
  run_id: string;
  messages: Message[];
  model?: string;
  agent?: string;  // Add agent parameter
}
```

---

## 4. Dependencies & Integration Points

### Backend Dependencies
1. Task 1.1 must complete first (registry system)
2. Task 1.2 depends on Task 1.1 (API uses registry)
3. Task 1.3 depends on Task 1.1 and 1.2 (endpoints use registry and API)
4. Task 1.4 is independent (configuration)

### Frontend Dependencies
1. Task 3.1 must complete first (types)
2. Task 3.2 depends on Task 3.1 (API client uses types)
3. Task 3.4 depends on Task 3.1 and 3.2 (hook uses types and API)
4. Task 3.3 depends on Task 3.1 and 3.4 (component uses types and hook)
5. Task 3.5 depends on Task 3.3 (header uses component)
6. Task 3.6 depends on Task 3.2 and 3.4 (hooks use API and selection hook)
7. Task 3.7 is independent (type update)

### Integration Dependencies
- Backend Task 1.2 must complete before Frontend Task 3.2 (API endpoint)
- Frontend components can be built in parallel with backend once types are defined

---

## 5. Testing Strategy

### Backend Testing
1. **Unit Tests**: Test AgentRegistry registration and retrieval
2. **API Tests**: Test `/api/agents` endpoint response format
3. **Integration Tests**: Test agent selection in chat/canvas endpoints
4. **Error Handling**: Test invalid agent IDs and unavailable agents

### Frontend Testing
1. **Component Tests**: Test AgentSelector rendering and interaction
2. **Hook Tests**: Test useAgentSelection loading and persistence
3. **Integration Tests**: Test agent selection flow end-to-end
4. **Visual Tests**: Verify positioning alongside ModelSelector

### Manual Testing Checklist
- [ ] Agent selector displays in header
- [ ] Available agents load from backend
- [ ] Agent selection persists across page reloads
- [ ] Selected agent is passed to chat/canvas endpoints
- [ ] Invalid agent selection shows error
- [ ] Default agent is used when none selected
- [ ] Agent selector works alongside model selector
- [ ] UI is responsive on mobile devices

---

## 6. Future Extensibility

This design supports future agents:

1. **Backend**: Register new agents in AgentRegistry
   ```python
   agent_registry.register_agent(AgentMetadata(
       id="new_agent",
       name="New Agent",
       description="New capabilities",
       icon="icon-name",
       available=True,
       sub_agents=["sub1", "sub2"],
       features=["feature1", "feature2"]
   ))
   ```

2. **Backend**: Add graph selection logic in endpoints
   ```python
   elif input_data.agent == "new_agent":
       graph = create_new_agent_graph(model=input_data.model)
   ```

3. **Frontend**: Automatically displays in AgentSelector (no code changes needed)

### Potential Future Enhancements
- Agent capabilities detection (e.g., supports file upload, voice input)
- Agent-specific UI customization
- Agent performance metrics in selector
- Agent grouping/categories for many agents
- Agent search/filter in dropdown
- Agent recommendation based on user query
- Per-agent configuration options

---

## 7. Implementation Order

### Phase 1: Backend Foundation (Backend Agent)
1. Create AgentRegistry system (Task 1.1)
2. Add /api/agents endpoint (Task 1.2)
3. Update configuration (Task 1.4)

### Phase 2: Backend Integration (Backend Agent)
4. Update request models (Task 1.3)
5. Update routing logic (Task 1.3)

### Phase 3: Frontend Foundation (Frontend Agent)
6. Create agent types (Task 3.1)
7. Add API client function (Task 3.2)
8. Create agent selection hook (Task 3.4)

### Phase 4: Frontend UI (Frontend Agent)
9. Create AgentSelector component (Task 3.3)
10. Update Header component (Task 3.5)
11. Update chat request types (Task 3.7)

### Phase 5: Integration (Frontend Agent)
12. Update useMessages hook (Task 3.6)
13. Update useCanvasChat hook (Task 3.6)

### Phase 6: Testing & Refinement
14. Backend testing
15. Frontend testing
16. Integration testing
17. UI/UX refinement

---

## 8. Success Criteria

- [ ] Backend `/api/agents` endpoint returns list of agents
- [ ] Frontend displays agent selector in header
- [ ] User can select different agents
- [ ] Selection persists across sessions
- [ ] Selected agent is used for chat/canvas requests
- [ ] Invalid agents are handled gracefully
- [ ] UI is consistent with existing ModelSelector
- [ ] System supports easy addition of future agents
- [ ] All tests pass
- [ ] Documentation is updated

---

## Notes

- Agent registry is designed for easy extensibility
- Frontend automatically adapts to new agents without code changes
- Agent selection is independent of model selection
- Both selectors coexist in header for clear UX
- System supports per-agent features and capabilities
- Sub-agents are tracked but not exposed in initial UI (future enhancement)
