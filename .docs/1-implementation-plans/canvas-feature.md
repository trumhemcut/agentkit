# Canvas Feature Implementation Plan

## Overview
Add Open Canvas-inspired functionality to AgentKit - a split-view interface where chat interactions on the left generate and edit artifacts (code/text) displayed on the right. This creates a better UX for content creation and coding with LLM agents.

## Reference Architecture
Based on LangChain's Open Canvas: https://github.com/langchain-ai/open-canvas
- **Key Concept**: Split-view interface with chat on left, live artifact rendering on right
- **Artifact Types**: Code files (with syntax highlighting) and Rich text (markdown)
- **Interaction Model**: Direct artifact editing, text selection with inline editing, version history navigation

## 1. Backend (LangGraph + AG-UI)

### 1.1 State Schema Updates
**File**: `backend/graphs/chat_graph.py`

Update state schema to support artifacts:

```python
from typing import TypedDict, Literal, Optional, List
from langgraph.graph import MessagesState

class ArtifactContentCode(TypedDict):
    index: int
    type: Literal["code"]
    title: str
    code: str
    language: str  # python, javascript, typescript, etc.

class ArtifactContentText(TypedDict):
    index: int
    type: Literal["text"]
    title: str
    fullMarkdown: str

class ArtifactV3(TypedDict):
    currentIndex: int
    contents: List[ArtifactContentCode | ArtifactContentText]

class CanvasGraphState(MessagesState):
    """Extended state for canvas feature"""
    artifact: Optional[ArtifactV3]
    selectedText: Optional[dict]  # {start: int, end: int, text: str}
    artifactAction: Optional[str]  # "create", "update", "rewrite"
```

### 1.2 Canvas Agent
**New File**: `backend/agents/canvas_agent.py`

Create specialized agent for artifact generation:

```python
from backend.agents.base_agent import BaseAgent
from backend.protocols.event_types import EventType

class CanvasAgent(BaseAgent):
    """Agent that generates and modifies artifacts"""
    
    async def process(self, state: CanvasGraphState) -> CanvasGraphState:
        """
        1. Detect if message requires artifact creation/modification
        2. Generate/update artifact content
        3. Emit AG-UI events for artifact streaming
        """
        
        # Emit THINKING event
        await self.emit_event(EventType.THINKING, {"message": "Analyzing request..."})
        
        # Determine action based on conversation context
        action = self._detect_artifact_action(state)
        
        if action == "create":
            artifact = await self._create_artifact(state)
        elif action == "update":
            artifact = await self._update_artifact(state)
        elif action == "rewrite":
            artifact = await self._rewrite_artifact(state)
        
        # Emit ARTIFACT_UPDATED event
        await self.emit_event(EventType.ARTIFACT_UPDATED, {
            "artifact": artifact,
            "action": action
        })
        
        return {**state, "artifact": artifact}
    
    def _detect_artifact_action(self, state) -> str:
        """Use LLM to classify user intent"""
        # Classify: create new, update existing, or rewrite
        pass
    
    async def _create_artifact(self, state) -> ArtifactV3:
        """Generate new artifact from scratch"""
        pass
    
    async def _update_artifact(self, state) -> ArtifactV3:
        """Update specific parts of existing artifact"""
        pass
    
    async def _rewrite_artifact(self, state) -> ArtifactV3:
        """Rewrite entire artifact with new approach"""
        pass
```

### 1.3 Canvas Tools
**New File**: `backend/tools/canvas_tools.py`

Create tools for artifact manipulation:

```python
from backend.tools.base_tool import BaseTool

class ExtractCodeTool(BaseTool):
    """Extract code from artifact for analysis"""
    name = "extract_code"
    description = "Extract code from current artifact"

class UpdateCodeBlockTool(BaseTool):
    """Update specific code block in artifact"""
    name = "update_code_block"
    description = "Update code at specific line range"

class ConvertArtifactTypeTool(BaseTool):
    """Convert between code and text artifacts"""
    name = "convert_artifact"
    description = "Convert artifact type (code <-> text)"
```

### 1.4 Canvas Graph
**New File**: `backend/graphs/canvas_graph.py`

Create LangGraph workflow for canvas operations:

```python
from langgraph.graph import StateGraph, END
from backend.agents.canvas_agent import CanvasAgent
from backend.graphs.chat_graph import ChatGraphState

def create_canvas_graph():
    """Build canvas workflow graph"""
    
    canvas_agent = CanvasAgent(name="canvas_agent")
    
    graph = StateGraph(CanvasGraphState)
    
    # Nodes
    graph.add_node("detect_intent", detect_intent_node)
    graph.add_node("canvas_agent", canvas_agent.process)
    graph.add_node("update_artifact", update_artifact_node)
    graph.add_node("chat_response", chat_response_node)
    
    # Edges
    graph.set_entry_point("detect_intent")
    
    graph.add_conditional_edges(
        "detect_intent",
        route_to_handler,
        {
            "artifact_action": "canvas_agent",
            "chat_only": "chat_response",
        }
    )
    
    graph.add_edge("canvas_agent", "update_artifact")
    graph.add_edge("update_artifact", END)
    graph.add_edge("chat_response", END)
    
    return graph.compile()

def detect_intent_node(state: CanvasGraphState) -> CanvasGraphState:
    """Classify if message requires artifact manipulation"""
    # Use LLM to classify: needs artifact or just chat
    pass

def route_to_handler(state: CanvasGraphState) -> str:
    """Route based on detected intent"""
    if state.get("artifactAction"):
        return "artifact_action"
    return "chat_only"

def update_artifact_node(state: CanvasGraphState) -> CanvasGraphState:
    """Finalize artifact updates"""
    pass

def chat_response_node(state: CanvasGraphState) -> CanvasGraphState:
    """Handle non-artifact chat messages"""
    pass
```

### 1.5 API Updates
**File**: `backend/api/routes.py`

Add canvas-specific endpoints:

```python
from fastapi import APIRouter, HTTPException
from backend.graphs.canvas_graph import create_canvas_graph

canvas_router = APIRouter(prefix="/canvas")

@canvas_router.post("/stream")
async def stream_canvas_message(request: CanvasMessageRequest):
    """Stream canvas agent response with artifact updates"""
    graph = create_canvas_graph()
    
    async def event_generator():
        async for event in graph.astream(request.state):
            yield encode_sse_event(event)
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@canvas_router.post("/artifacts/{artifact_id}")
async def update_artifact(artifact_id: str, updates: ArtifactUpdate):
    """Manually update artifact content"""
    pass

@canvas_router.get("/artifacts/{artifact_id}/versions")
async def get_artifact_versions(artifact_id: str):
    """Get version history for artifact"""
    pass
```

### 1.6 AG-UI Protocol Extensions
**File**: `backend/protocols/event_types.py`

Add canvas-specific event types:

```python
class EventType(str, Enum):
    # Existing events...
    
    # Canvas-specific events
    ARTIFACT_CREATED = "artifact_created"
    ARTIFACT_UPDATED = "artifact_updated"
    ARTIFACT_STREAMING = "artifact_streaming"  # For streaming artifact content
    ARTIFACT_VERSION_CHANGED = "artifact_version_changed"
    SELECTION_CONTEXT = "selection_context"  # When user selects text
```

**File**: `backend/protocols/event_encoder.py`

Update encoder for artifact events:

```python
def encode_artifact_event(event_type: EventType, artifact: ArtifactV3, metadata: dict) -> dict:
    """Encode artifact-related events for frontend"""
    return {
        "type": event_type.value,
        "artifact": artifact,
        "metadata": metadata,
        "timestamp": datetime.utcnow().isoformat()
    }
```

---

## 2. AG-UI Protocol (Communication Contract)

### 2.1 Message Formats

#### Backend → Frontend

**Artifact Created Event**
```typescript
{
  type: "artifact_created",
  artifact: {
    currentIndex: 1,
    contents: [{
      index: 1,
      type: "code" | "text",
      title: string,
      code?: string,        // for type="code"
      language?: string,    // for type="code"
      fullMarkdown?: string // for type="text"
    }]
  },
  timestamp: string
}
```

**Artifact Streaming Event** (for real-time updates during generation)
```typescript
{
  type: "artifact_streaming",
  contentDelta: string,  // Incremental content chunk
  artifactIndex: number,
  timestamp: string
}
```

**Artifact Version Changed Event**
```typescript
{
  type: "artifact_version_changed",
  artifact: ArtifactV3,
  previousIndex: number,
  currentIndex: number,
  timestamp: string
}
```

#### Frontend → Backend

**Canvas Message Request**
```typescript
{
  message: string,
  artifact?: ArtifactV3,          // Current artifact state
  selectedText?: {                 // If user selected text
    start: number,
    end: number,
    text: string
  },
  action?: "create" | "update" | "rewrite" | "chat"
}
```

### 2.2 State Synchronization

- **Artifact State**: Backend holds canonical artifact state, streams to frontend
- **Version History**: Backend maintains all versions, frontend can request specific version
- **Selection State**: Frontend tracks selection, sends context to backend when needed
- **Edit Conflicts**: Backend merges user edits with agent suggestions

---

## 3. Frontend (NextJS + Shadcn UI + AG-UI)

### 3.1 Canvas Layout Component
**New File**: `frontend/components/Canvas/CanvasLayout.tsx`

Main canvas split-view component:

```typescript
import { ResizablePanel, ResizablePanelGroup, ResizableHandle } from "@/components/ui/resizable"

interface CanvasLayoutProps {
  chatPanel: React.ReactNode
  artifactPanel: React.ReactNode
}

export function CanvasLayout({ chatPanel, artifactPanel }: CanvasLayoutProps) {
  return (
    <ResizablePanelGroup direction="horizontal" className="h-screen">
      {/* Chat Panel (Left) */}
      <ResizablePanel defaultSize={40} minSize={30} maxSize={60}>
        {chatPanel}
      </ResizablePanel>
      
      <ResizableHandle />
      
      {/* Artifact Panel (Right) */}
      <ResizablePanel defaultSize={60} minSize={40}>
        {artifactPanel}
      </ResizablePanel>
    </ResizablePanelGroup>
  )
}
```

### 3.2 Artifact Renderer Component
**New File**: `frontend/components/Canvas/ArtifactRenderer.tsx`

Displays and allows editing of artifacts:

```typescript
import { CodeRenderer } from "./CodeRenderer"
import { TextRenderer } from "./TextRenderer"
import { ArtifactHeader } from "./ArtifactHeader"

interface ArtifactRendererProps {
  artifact: ArtifactV3 | null
  isStreaming: boolean
  onArtifactUpdate: (content: string, index: number) => void
  onVersionChange: (index: number) => void
}

export function ArtifactRenderer({ 
  artifact, 
  isStreaming, 
  onArtifactUpdate,
  onVersionChange 
}: ArtifactRendererProps) {
  if (!artifact) {
    return <EmptyArtifactState />
  }
  
  const currentContent = artifact.contents.find(c => c.index === artifact.currentIndex)
  
  return (
    <div className="flex flex-col h-full">
      <ArtifactHeader
        title={currentContent?.title}
        currentVersion={artifact.currentIndex}
        totalVersions={artifact.contents.length}
        onVersionChange={onVersionChange}
      />
      
      <div className="flex-1 overflow-auto">
        {currentContent?.type === "code" ? (
          <CodeRenderer
            code={currentContent.code}
            language={currentContent.language}
            isStreaming={isStreaming}
            onUpdate={(newCode) => onArtifactUpdate(newCode, artifact.currentIndex)}
          />
        ) : (
          <TextRenderer
            markdown={currentContent?.fullMarkdown || ""}
            isStreaming={isStreaming}
            onUpdate={(newMarkdown) => onArtifactUpdate(newMarkdown, artifact.currentIndex)}
          />
        )}
      </div>
    </div>
  )
}
```

### 3.3 Code Renderer Component
**New File**: `frontend/components/Canvas/CodeRenderer.tsx`

Syntax-highlighted code editor:

```typescript
import CodeMirror from "@uiw/react-codemirror"
import { javascript } from "@codemirror/lang-javascript"
import { python } from "@codemirror/lang-python"
// Import other language support

interface CodeRendererProps {
  code: string
  language: string
  isStreaming: boolean
  onUpdate: (newCode: string) => void
}

export function CodeRenderer({ code, language, isStreaming, onUpdate }: CodeRendererProps) {
  const extensions = [getLanguageExtension(language)]
  
  return (
    <div className="relative h-full">
      <CodeMirror
        value={code}
        extensions={extensions}
        onChange={onUpdate}
        editable={!isStreaming}
        className={isStreaming ? "pulse-animation" : ""}
      />
      
      {isStreaming && (
        <div className="absolute top-2 right-2">
          <StreamingIndicator />
        </div>
      )}
    </div>
  )
}

function getLanguageExtension(language: string) {
  const languageMap: Record<string, any> = {
    javascript: javascript(),
    python: python(),
    // Add more languages
  }
  return languageMap[language] || []
}
```

### 3.4 Text Renderer Component
**New File**: `frontend/components/Canvas/TextRenderer.tsx`

Rich markdown editor:

```typescript
import { useCreateBlockNote } from "@blocknote/react"
import { BlockNoteView } from "@blocknote/shadcn"
import "@blocknote/shadcn/style.css"

interface TextRendererProps {
  markdown: string
  isStreaming: boolean
  onUpdate: (newMarkdown: string) => void
}

export function TextRenderer({ markdown, isStreaming, onUpdate }: TextRendererProps) {
  const editor = useCreateBlockNote()
  
  useEffect(() => {
    // Parse markdown to blocks
    if (markdown) {
      editor.tryParseMarkdownToBlocks(markdown).then(blocks => {
        editor.replaceBlocks(editor.document, blocks)
      })
    }
  }, [markdown, editor])
  
  const handleChange = async () => {
    if (!isStreaming) {
      const fullMarkdown = await editor.blocksToMarkdownLossy(editor.document)
      onUpdate(fullMarkdown)
    }
  }
  
  return (
    <div className="p-4 h-full">
      <BlockNoteView
        editor={editor}
        onChange={handleChange}
        editable={!isStreaming}
      />
    </div>
  )
}
```

### 3.5 Artifact Header Component
**New File**: `frontend/components/Canvas/ArtifactHeader.tsx`

Header with title and version navigation:

```typescript
import { Button } from "@/components/ui/button"
import { ChevronLeft, ChevronRight } from "lucide-react"

interface ArtifactHeaderProps {
  title?: string
  currentVersion: number
  totalVersions: number
  onVersionChange: (version: number) => void
}

export function ArtifactHeader({ 
  title, 
  currentVersion, 
  totalVersions, 
  onVersionChange 
}: ArtifactHeaderProps) {
  const canGoPrevious = currentVersion > 1
  const canGoNext = currentVersion < totalVersions
  
  return (
    <div className="flex items-center justify-between p-4 border-b">
      <h2 className="text-lg font-semibold">{title || "Untitled"}</h2>
      
      {totalVersions > 1 && (
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="icon"
            disabled={!canGoPrevious}
            onClick={() => onVersionChange(currentVersion - 1)}
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          
          <span className="text-sm text-gray-600">
            {currentVersion} / {totalVersions}
          </span>
          
          <Button
            variant="ghost"
            size="icon"
            disabled={!canGoNext}
            onClick={() => onVersionChange(currentVersion + 1)}
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      )}
    </div>
  )
}
```

### 3.6 Canvas Context & State Management
**New File**: `frontend/contexts/CanvasContext.tsx`

Canvas-specific state management:

```typescript
import { createContext, useContext, useState, useCallback } from "react"

interface CanvasContextValue {
  artifact: ArtifactV3 | null
  setArtifact: (artifact: ArtifactV3 | null) => void
  isArtifactStreaming: boolean
  setIsArtifactStreaming: (streaming: boolean) => void
  updateArtifactContent: (content: string, index: number) => void
  changeArtifactVersion: (index: number) => void
}

const CanvasContext = createContext<CanvasContextValue | null>(null)

export function CanvasProvider({ children }: { children: React.ReactNode }) {
  const [artifact, setArtifact] = useState<ArtifactV3 | null>(null)
  const [isArtifactStreaming, setIsArtifactStreaming] = useState(false)
  
  const updateArtifactContent = useCallback((content: string, index: number) => {
    setArtifact(prev => {
      if (!prev) return null
      
      const updatedContents = prev.contents.map(c => 
        c.index === index
          ? { ...c, ...(c.type === "code" ? { code: content } : { fullMarkdown: content }) }
          : c
      )
      
      return { ...prev, contents: updatedContents }
    })
  }, [])
  
  const changeArtifactVersion = useCallback((index: number) => {
    setArtifact(prev => {
      if (!prev) return null
      return { ...prev, currentIndex: index }
    })
  }, [])
  
  return (
    <CanvasContext.Provider
      value={{
        artifact,
        setArtifact,
        isArtifactStreaming,
        setIsArtifactStreaming,
        updateArtifactContent,
        changeArtifactVersion,
      }}
    >
      {children}
    </CanvasContext.Provider>
  )
}

export function useCanvas() {
  const context = useContext(CanvasContext)
  if (!context) throw new Error("useCanvas must be used within CanvasProvider")
  return context
}
```

### 3.7 AG-UI Client Integration
**Update File**: `frontend/services/agui-client.ts`

Add canvas event handlers:

```typescript
// Existing AG-UI client...

export function handleCanvasEvents(eventSource: EventSource, callbacks: {
  onArtifactCreated: (artifact: ArtifactV3) => void
  onArtifactStreaming: (delta: string, index: number) => void
  onArtifactUpdated: (artifact: ArtifactV3) => void
  onVersionChanged: (artifact: ArtifactV3) => void
}) {
  eventSource.addEventListener("artifact_created", (event) => {
    const data = JSON.parse(event.data)
    callbacks.onArtifactCreated(data.artifact)
  })
  
  eventSource.addEventListener("artifact_streaming", (event) => {
    const data = JSON.parse(event.data)
    callbacks.onArtifactStreaming(data.contentDelta, data.artifactIndex)
  })
  
  eventSource.addEventListener("artifact_updated", (event) => {
    const data = JSON.parse(event.data)
    callbacks.onArtifactUpdated(data.artifact)
  })
  
  eventSource.addEventListener("artifact_version_changed", (event) => {
    const data = JSON.parse(event.data)
    callbacks.onVersionChanged(data.artifact)
  })
}
```

### 3.8 Canvas Page Component
**New File**: `frontend/app/canvas/page.tsx`

Main canvas page:

```typescript
"use client"

import { CanvasLayout } from "@/components/Canvas/CanvasLayout"
import { ArtifactRenderer } from "@/components/Canvas/ArtifactRenderer"
import { ChatContainer } from "@/components/ChatContainer"
import { CanvasProvider, useCanvas } from "@/contexts/CanvasContext"
import { useAGUI } from "@/hooks/useAGUI"
import { handleCanvasEvents } from "@/services/agui-client"

function CanvasPageContent() {
  const { 
    artifact, 
    setArtifact, 
    isArtifactStreaming, 
    setIsArtifactStreaming,
    updateArtifactContent,
    changeArtifactVersion 
  } = useCanvas()
  
  const { sendMessage } = useAGUI({
    onEvent: (eventSource) => {
      handleCanvasEvents(eventSource, {
        onArtifactCreated: (artifact) => {
          setArtifact(artifact)
          setIsArtifactStreaming(false)
        },
        onArtifactStreaming: (delta, index) => {
          setIsArtifactStreaming(true)
          // Append delta to artifact content
        },
        onArtifactUpdated: (artifact) => {
          setArtifact(artifact)
          setIsArtifactStreaming(false)
        },
        onVersionChanged: (artifact) => {
          setArtifact(artifact)
        },
      })
    }
  })
  
  return (
    <CanvasLayout
      chatPanel={
        <ChatContainer
          onSendMessage={sendMessage}
          showArtifactSuggestions={!artifact}
        />
      }
      artifactPanel={
        <ArtifactRenderer
          artifact={artifact}
          isStreaming={isArtifactStreaming}
          onArtifactUpdate={updateArtifactContent}
          onVersionChange={changeArtifactVersion}
        />
      }
    />
  )
}

export default function CanvasPage() {
  return (
    <CanvasProvider>
      <CanvasPageContent />
    </CanvasProvider>
  )
}
```

### 3.9 TypeScript Types
**New File**: `frontend/types/canvas.ts`

Canvas-specific type definitions:

```typescript
export interface ArtifactContentCode {
  index: number
  type: "code"
  title: string
  code: string
  language: string
}

export interface ArtifactContentText {
  index: number
  type: "text"
  title: string
  fullMarkdown: string
}

export type ArtifactContent = ArtifactContentCode | ArtifactContentText

export interface ArtifactV3 {
  currentIndex: number
  contents: ArtifactContent[]
}

export interface CanvasMessage {
  message: string
  artifact?: ArtifactV3
  selectedText?: {
    start: number
    end: number
    text: string
  }
  action?: "create" | "update" | "rewrite" | "chat"
}

export interface CanvasEventData {
  type: "artifact_created" | "artifact_streaming" | "artifact_updated" | "artifact_version_changed"
  artifact?: ArtifactV3
  contentDelta?: string
  artifactIndex?: number
  timestamp: string
}
```

---

## 4. Integration Points

### 4.1 Navigation
**Update**: `frontend/components/Sidebar.tsx`

Add canvas mode navigation:

```typescript
<nav>
  <Link href="/">Chat Mode</Link>
  <Link href="/canvas">Canvas Mode</Link>  {/* NEW */}
</nav>
```

### 4.2 Thread Persistence
**Backend**: Store artifact state in thread metadata
**Frontend**: Save/restore artifact from localStorage

```typescript
// In thread metadata
{
  threadId: "...",
  artifact: ArtifactV3 | null,
  canvasMode: boolean
}
```

---

## 5. Implementation Sequence

### Phase 1: Core Infrastructure (Backend Lead)
1. ✅ Update state schemas with artifact types
2. ✅ Create `CanvasAgent` with basic artifact generation
3. ✅ Add AG-UI protocol events for artifacts
4. ✅ Create canvas graph with routing logic
5. ✅ Add canvas API endpoints

### Phase 2: Basic UI (Frontend Lead)
1. ✅ Create `CanvasLayout` with resizable panels
2. ✅ Implement `ArtifactRenderer` component
3. ✅ Build `CodeRenderer` with syntax highlighting
4. ✅ Build `TextRenderer` with markdown support
5. ✅ Add `ArtifactHeader` with version navigation

### Phase 3: State Management & Integration
1. ✅ Create `CanvasContext` for state management
2. ✅ Integrate AG-UI client with canvas events
3. ✅ Connect chat panel to canvas workflow
4. ✅ Implement artifact streaming from backend to frontend
5. ✅ Add canvas page route

### Phase 4: Advanced Features
1. ⬜ Text selection and inline editing
2. ⬜ Artifact quick actions toolbar
3. ⬜ Export artifact functionality
4. ⬜ Artifact templates for quick start
5. ⬜ Multi-artifact management

### Phase 5: Polish & Optimization
1. ⬜ Add loading states and animations
2. ⬜ Improve streaming performance
3. ⬜ Error handling and recovery
4. ⬜ Accessibility improvements
5. ⬜ Testing and documentation

---

## 6. Dependencies & Package Requirements

### Backend
```bash
# No new packages needed - use existing LangGraph, FastAPI, AG-UI
```

### Frontend
```bash
npm install @uiw/react-codemirror @codemirror/lang-javascript @codemirror/lang-python
npm install @blocknote/react @blocknote/shadcn @blocknote/core
npm install lucide-react  # Already installed
```

---

## 7. Testing Strategy

### Backend Testing
- **Unit tests**: Canvas agent logic, artifact generation
- **Integration tests**: Canvas graph workflow, API endpoints
- **Stream tests**: Verify AG-UI event emission

### Frontend Testing
- **Component tests**: Each canvas component in isolation
- **Integration tests**: Full canvas workflow with mock backend
- **E2E tests**: Real user flows (create artifact, edit, navigate versions)

---

## 8. Rollout Plan

1. **Feature Flag**: Enable canvas mode behind a feature flag
2. **Beta Access**: Invite select users to test canvas mode
3. **Feedback Loop**: Collect user feedback and iterate
4. **General Availability**: Release to all users
5. **Default Mode**: Consider making canvas the default experience

---

## 9. Known Limitations & Future Enhancements

### Current Limitations
- Single artifact per thread (future: multi-artifact)
- Basic version history (future: Git-like branching)
- Limited language support (future: expand to 20+ languages)

### Future Enhancements
- **Collaborative Editing**: Real-time multi-user editing
- **Artifact Templates**: Pre-built templates for common tasks
- **Export Options**: Download as file, share as gist
- **Execution Environment**: Run code artifacts directly in browser
- **Visual Diff**: Show changes between versions
- **Artifact Search**: Search across all artifacts in thread history

---

## 10. Success Metrics

- **User Engagement**: % of users who try canvas mode
- **Artifact Creation**: Average artifacts created per session
- **Edit Frequency**: How often users manually edit artifacts
- **Version Navigation**: % of users navigating artifact history
- **Session Duration**: Time spent in canvas mode vs. chat mode
- **Conversion**: Users who switch from chat to canvas mode

---

## References

- **Open Canvas Repository**: https://github.com/langchain-ai/open-canvas
- **LangGraph Documentation**: https://langchain-ai.github.io/langgraph/
- **AG-UI Protocol**: https://context7.com/ag-ui-protocol/ag-ui
- **BlockNote Editor**: https://www.blocknotejs.org/
- **CodeMirror**: https://codemirror.net/

---

## Questions for Clarification

1. Should canvas mode replace chat mode or coexist as separate routes?
2. Do we need artifact persistence beyond the current thread?
3. Should we support multi-artifact workflows (e.g., multiple code files)?
4. What programming languages should we prioritize for syntax highlighting?
5. Should artifacts be exportable/shareable outside the app?
