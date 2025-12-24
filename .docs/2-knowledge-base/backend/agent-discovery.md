# Agent Discovery System

## Overview

The Agent Discovery System provides a centralized registry for managing and discovering available agents in the backend. It enables the frontend to dynamically list available agents and allows users to select which agent to use for their conversations.

## Architecture

### Components

1. **Agent Registry** (`backend/agents/agent_registry.py`)
   - Centralized registry for agent metadata
   - Singleton pattern for global access
   - Manages agent availability and features

2. **Agent Discovery API** (`backend/api/routes.py`)
   - GET `/api/agents` endpoint for listing agents
   - Returns agent metadata and default selection

3. **Agent Selection** (`backend/api/models.py`, `backend/api/routes.py`)
   - Request models include `agent` parameter
   - Endpoints validate and route based on agent selection
   - Dynamic graph selection based on agent ID

## Agent Registry

### AgentMetadata

Dataclass describing an agent's properties:

```python
@dataclass
class AgentMetadata:
    id: str              # Unique identifier (e.g., "chat", "canvas")
    name: str            # Display name (e.g., "Chat Agent")
    description: str     # Brief description of capabilities
    icon: str            # Icon identifier for frontend
    available: bool      # Whether agent is currently available
    sub_agents: List[str]  # List of sub-agent IDs in graph
    features: List[str]    # List of feature tags
```

### AgentRegistry Class

Singleton registry managing all agents:

```python
class AgentRegistry:
    def __init__(self):
        self._agents: Dict[str, AgentMetadata] = {}
        self._initialize_agents()
    
    def register_agent(self, metadata: AgentMetadata):
        """Register a new agent"""
        
    def get_agent(self, agent_id: str) -> Optional[AgentMetadata]:
        """Get agent metadata by ID"""
        
    def list_agents(self, available_only: bool = True) -> List[AgentMetadata]:
        """List all registered agents"""
        
    def is_available(self, agent_id: str) -> bool:
        """Check if agent is available"""
```

### Registered Agents

#### Chat Agent
- **ID**: `chat`
- **Name**: Chat Agent
- **Description**: General purpose conversational agent
- **Icon**: `message-circle`
- **Sub-agents**: None
- **Features**: `conversation`, `streaming`

#### Canvas Agent
- **ID**: `canvas`
- **Name**: Canvas Agent
- **Description**: Multi-agent system with artifact generation and editing
- **Icon**: `layout`
- **Sub-agents**: `generator`, `editor`
- **Features**: `artifacts`, `code-generation`, `multi-step`

## API Endpoints

### GET /api/agents

Returns list of available agents with metadata.

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

**Error Handling**:
- Returns HTTP 500 if registry fails to load
- Includes error message in detail field

### POST /api/chat (with agent parameter)

Chat endpoint now accepts optional `agent` parameter to specify which agent to use.

**Request Body**:
```json
{
  "thread_id": "string",
  "run_id": "string",
  "messages": [...],
  "model": "string",
  "agent": "chat"  // Optional, defaults to "chat"
}
```

**Agent Validation**:
- Validates agent ID before starting streaming
- Returns HTTP 400 if agent is not available
- Returns HTTP 400 if agent ID is unknown
- Uses default agent if parameter is omitted

**Dynamic Routing**:
```python
if input_data.agent == "chat":
    graph = create_chat_graph(model=input_data.model)
elif input_data.agent == "canvas":
    graph = create_canvas_graph(model=input_data.model)
```

### POST /api/canvas/stream (with agent parameter)

Canvas endpoint also accepts optional `agent` parameter.

**Request Body**:
```json
{
  "thread_id": "string",
  "run_id": "string",
  "messages": [...],
  "artifact": {...},
  "selectedText": {...},
  "action": "create|update|rewrite|chat",
  "model": "string",
  "agent": "canvas"  // Optional, defaults to "canvas"
}
```

## Configuration

### Default Agent Setting

Added to `backend/config.py`:

```python
class Settings(BaseSettings):
    # ... other settings ...
    
    # Agent settings
    DEFAULT_AGENT: str = "chat"
```

Can be overridden via environment variable:
```bash
DEFAULT_AGENT=canvas python main.py
```

## Usage Patterns

### Registering a New Agent

To add a new agent to the system:

```python
from agents.agent_registry import agent_registry, AgentMetadata

# Register new agent
agent_registry.register_agent(AgentMetadata(
    id="new_agent",
    name="New Agent",
    description="Description of capabilities",
    icon="icon-name",
    available=True,
    sub_agents=["sub1", "sub2"],
    features=["feature1", "feature2"]
))
```

### Adding Graph for New Agent

Update routing logic in endpoints:

```python
# In /api/chat endpoint
if input_data.agent == "chat":
    graph = create_chat_graph(model=input_data.model)
elif input_data.agent == "canvas":
    graph = create_canvas_graph(model=input_data.model)
elif input_data.agent == "new_agent":
    graph = create_new_agent_graph(model=input_data.model)
else:
    raise ValueError(f"Unknown agent: {input_data.agent}")
```

### Checking Agent Availability

```python
from agents.agent_registry import agent_registry

if agent_registry.is_available("chat"):
    # Use chat agent
    pass
```

### Listing All Agents

```python
from agents.agent_registry import agent_registry

# Get all available agents
agents = agent_registry.list_agents(available_only=True)

for agent in agents:
    print(f"{agent.name}: {agent.description}")
```

## Error Handling

### Invalid Agent ID

When an unknown or unavailable agent is requested:

```python
# Returns HTTP 400
{
  "detail": "Agent 'unknown_agent' not available"
}
```

### Missing Agent Registry

If registry fails to initialize:

```python
# Returns HTTP 500
{
  "detail": "Error fetching agents: <error message>"
}
```

## Testing

### Unit Tests

Test agent registry functionality:

```python
from agents.agent_registry import agent_registry

# Test listing agents
agents = agent_registry.list_agents()
assert len(agents) == 2

# Test getting specific agent
chat_agent = agent_registry.get_agent("chat")
assert chat_agent.name == "Chat Agent"

# Test availability check
assert agent_registry.is_available("chat") == True
assert agent_registry.is_available("nonexistent") == False
```

### API Tests

Test agent discovery endpoint:

```python
import requests

response = requests.get("http://localhost:8000/api/agents")
assert response.status_code == 200

data = response.json()
assert "agents" in data
assert "default" in data
assert len(data["agents"]) > 0
```

### Agent Selection Tests

Test chat endpoint with agent parameter:

```python
import requests

# Valid agent
response = requests.post(
    "http://localhost:8000/api/chat",
    json={
        "thread_id": "test",
        "run_id": "test",
        "messages": [{"role": "user", "content": "Hello"}],
        "agent": "chat"
    }
)
assert response.status_code == 200

# Invalid agent
response = requests.post(
    "http://localhost:8000/api/chat",
    json={
        "thread_id": "test",
        "run_id": "test",
        "messages": [{"role": "user", "content": "Hello"}],
        "agent": "invalid"
    }
)
assert response.status_code == 400
```

## Frontend Integration

The agent discovery system enables the frontend to:

1. **Fetch Available Agents**
   ```typescript
   const response = await fetch('/api/agents');
   const { agents, default: defaultAgent } = await response.json();
   ```

2. **Display Agent Selector**
   - Show dropdown with available agents
   - Display agent names, icons, and descriptions
   - Remember user's selected agent

3. **Send Agent with Requests**
   ```typescript
   await fetch('/api/chat', {
     method: 'POST',
     body: JSON.stringify({
       thread_id,
       run_id,
       messages,
       model,
       agent: selectedAgent  // Include selected agent
     })
   });
   ```

## Best Practices

1. **Agent Registration**
   - Register agents at startup in `_initialize_agents()`
   - Use descriptive IDs (lowercase, no spaces)
   - Provide clear descriptions for users

2. **Availability Management**
   - Set `available=False` for agents under development
   - Disabled agents won't appear in frontend
   - Can be toggled without removing registration

3. **Error Handling**
   - Validate agent before starting streaming
   - Return meaningful error messages
   - Log errors for debugging

4. **Graph Selection**
   - Keep routing logic centralized in endpoints
   - Validate agent has corresponding graph
   - Provide fallback for unknown agents

5. **Feature Tags**
   - Use consistent feature names across agents
   - Enable feature-based filtering in future
   - Document what each feature means

## Future Enhancements

1. **Agent Capabilities**
   - Add capability detection (file upload, voice, etc.)
   - Enable/disable features based on capabilities

2. **Agent Configuration**
   - Per-agent configuration options
   - Agent-specific UI customization

3. **Agent Metrics**
   - Performance metrics per agent
   - Usage statistics
   - Recommendation engine

4. **Agent Grouping**
   - Categories for many agents
   - Search/filter functionality
   - Favorites/recent agents

5. **Dynamic Agent Loading**
   - Plugin-based agent system
   - Hot-reload agents without restart
   - Agent versioning

## Related Documentation

- [API Routes](./api/README.md) - API endpoint details
- [Agent Base Classes](./agents/README.md) - Agent implementation patterns
- [Configuration](./README.md#configuration) - Backend configuration
- [Frontend Agent Selection](../frontend/agent-selection.md) - Frontend integration
