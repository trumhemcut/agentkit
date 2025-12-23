# Canvas Feature Architecture Diagram

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                          FRONTEND (NextJS)                          │
│                                                                     │
│  ┌─────────────────────┐         ┌──────────────────────────────┐ │
│  │   Chat Panel        │         │     Artifact Panel           │ │
│  │                     │         │                              │ │
│  │  • Message History  │         │  • Code/Text Renderer        │ │
│  │  • Input Field      │         │  • Version Navigation        │ │
│  │  • Send Button      │         │  • Edit Capabilities         │ │
│  └─────────────────────┘         └──────────────────────────────┘ │
│              │                                  ▲                   │
│              │ User Message                    │ Artifact Display  │
│              ▼                                  │                   │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │              AG-UI Client (Event Handler)                    │ │
│  │  • Receives SSE events                                       │ │
│  │  • Updates artifact state                                    │ │
│  │  • Manages streaming                                         │ │
│  └──────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  │ HTTP POST (SSE)
                                  │ /canvas/stream
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      BACKEND (FastAPI + LangGraph)                  │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                    API Layer (routes.py)                     │ │
│  │                                                              │ │
│  │  POST /canvas/stream                                         │ │
│  │  ├─ Accepts: CanvasMessageRequest                           │ │
│  │  ├─ Returns: SSE Stream (AG-UI Events)                      │ │
│  │  └─ Handles: Error recovery                                 │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                  │                                  │
│                                  ▼                                  │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │              Canvas Graph (canvas_graph.py)                  │ │
│  │                                                              │ │
│  │    START → detect_intent → [conditional routing]            │ │
│  │                              │            │                  │ │
│  │                    artifact_action    chat_only             │ │
│  │                              │            │                  │ │
│  │                              ▼            ▼                  │ │
│  │                      ┌──────────┐  ┌──────────┐            │ │
│  │                      │ Canvas   │  │  Chat    │            │ │
│  │                      │ Agent    │  │  Agent   │            │ │
│  │                      └──────────┘  └──────────┘            │ │
│  │                              │            │                  │ │
│  │                              ▼            │                  │ │
│  │                      update_artifact      │                  │ │
│  │                              │            │                  │ │
│  │                              └────────────┘                  │ │
│  │                                  │                            │ │
│  │                                  ▼                            │ │
│  │                                 END                           │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                  │                                  │
│                                  ▼                                  │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │              Canvas Agent (canvas_agent.py)                  │ │
│  │                                                              │ │
│  │  Modes:                                                      │ │
│  │  ├─ run() → Streaming with AG-UI events                     │ │
│  │  └─ process_sync() → LangGraph node execution               │ │
│  │                                                              │ │
│  │  Operations:                                                 │ │
│  │  ├─ _create_artifact() → New artifact from scratch          │ │
│  │  ├─ _update_artifact() → Modify existing                    │ │
│  │  └─ _rewrite_artifact() → Complete regeneration             │ │
│  │                                                              │ │
│  │  Intelligence:                                               │ │
│  │  ├─ _detect_artifact_type() → code vs text                  │ │
│  │  ├─ _detect_language() → Python, JS, etc.                   │ │
│  │  └─ _extract_title() → Smart title generation               │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                  │                                  │
│                                  ▼                                  │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                    LLM Provider (Ollama)                     │ │
│  │                                                              │ │
│  │  Model: qwen:7b                                              │ │
│  │  Mode: Streaming                                             │ │
│  │  Endpoint: http://localhost:11434                           │ │
│  └──────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Artifact Creation Flow

```
User: "Write a Python factorial function"
  │
  ▼
POST /canvas/stream
  │
  ▼
detect_intent_node()
  ├─ Detects: "create" action
  ├─ Keywords: "write", "function"
  └─ Route: artifact_action
  │
  ▼
CanvasAgent.run()
  ├─ Emit: THINKING
  ├─ Detect type: code
  ├─ Detect language: python
  ├─ Create prompt: code generation
  │
  ▼
LLM Stream Response
  ├─ Emit: ARTIFACT_STREAMING_START
  ├─ Stream chunks: "def factorial(n):\n..."
  ├─ Emit: ARTIFACT_STREAMING (each chunk)
  │
  ▼
Process Complete
  ├─ Extract title: "Function: factorial"
  ├─ Create artifact: ArtifactV3
  ├─ Emit: ARTIFACT_CREATED
  │
  ▼
Client Receives Artifact
  ├─ Display in Code Renderer
  └─ Enable editing
```

### 2. Artifact Update Flow

```
User: "Add error handling"
  │
  ▼
POST /canvas/stream (with artifact)
  │
  ▼
detect_intent_node()
  ├─ Detects: "update" action
  ├─ Keywords: "add"
  ├─ Has artifact: true
  └─ Route: artifact_action
  │
  ▼
CanvasAgent.run()
  ├─ Emit: THINKING
  ├─ Load current artifact
  ├─ Create context prompt
  │   └─ Includes current code
  │
  ▼
LLM Stream Response
  ├─ Emit: ARTIFACT_STREAMING_START
  ├─ Stream updated code
  ├─ Emit: ARTIFACT_STREAMING
  │
  ▼
Process Complete
  ├─ Create version 2
  ├─ Update currentIndex: 2
  ├─ Preserve version 1 in contents[]
  ├─ Emit: ARTIFACT_UPDATED
  │
  ▼
Client Receives Updated Artifact
  ├─ Display new version
  └─ Version navigation: [1] [2] ←
```

## State Structure

```
CanvasGraphState:
┌─────────────────────────────────────┐
│ messages: [                         │
│   {role: "user", content: "..."},  │
│   {role: "assistant", content: ""}, │
│ ]                                   │
│                                     │
│ thread_id: "uuid"                   │
│ run_id: "uuid"                      │
│                                     │
│ artifact: {                         │
│   currentIndex: 2,                  │
│   contents: [                       │
│     {  // Version 1                 │
│       index: 1,                     │
│       type: "code",                 │
│       title: "Factorial Function",  │
│       code: "def factorial(n):...", │
│       language: "python"            │
│     },                              │
│     {  // Version 2                 │
│       index: 2,                     │
│       type: "code",                 │
│       title: "Factorial Function",  │
│       code: "def factorial(n):...   │
│              # with error handling",│
│       language: "python"            │
│     }                               │
│   ]                                 │
│ }                                   │
│                                     │
│ selectedText: null                  │
│ artifactAction: "update"            │
└─────────────────────────────────────┘
```

## Event Stream Sequence

```
Time │ Event                    │ Data
─────┼──────────────────────────┼─────────────────────────────
  0s │ RUN_STARTED              │ {thread_id, run_id}
     │                          │
  1s │ THINKING                 │ {message: "Processing..."}
     │                          │
  2s │ ARTIFACT_STREAMING_START │ {artifactType: "code"}
     │                          │
  3s │ ARTIFACT_STREAMING       │ {contentDelta: "def ", index: 1}
  3s │ ARTIFACT_STREAMING       │ {contentDelta: "factorial", index: 1}
  4s │ ARTIFACT_STREAMING       │ {contentDelta: "(n):\n", index: 1}
  4s │ ARTIFACT_STREAMING       │ {contentDelta: "    return ", index: 1}
  5s │ ARTIFACT_STREAMING       │ {contentDelta: "1 if n <= 1...", index: 1}
     │                          │
  6s │ ARTIFACT_CREATED         │ {artifact: {...}}
     │                          │
  6s │ RUN_FINISHED             │ {thread_id, run_id}
```

## Component Interaction

```
┌──────────────┐
│   User       │
└──────┬───────┘
       │
       │ 1. Send message with/without artifact
       ▼
┌──────────────────────┐
│   API Endpoint       │
│   /canvas/stream     │
└──────┬───────────────┘
       │
       │ 2. Create state
       ▼
┌──────────────────────┐
│  Intent Detection    │
│  • Keyword analysis  │
│  • Artifact presence │
└──────┬───────────────┘
       │
       │ 3. Route
       ├───────────────┬──────────────┐
       ▼               ▼              ▼
┌──────────┐    ┌──────────┐  ┌──────────┐
│  Create  │    │  Update  │  │   Chat   │
│  Agent   │    │  Agent   │  │  Agent   │
└────┬─────┘    └────┬─────┘  └────┬─────┘
     │               │             │
     │               │             │
     │ 4. Process with LLM        │
     │               │             │
     ▼               ▼             ▼
┌─────────────────────────────────────┐
│        Stream AG-UI Events          │
│  • thinking                         │
│  • artifact_streaming               │
│  • artifact_created/updated         │
└─────────────┬───────────────────────┘
              │
              │ 5. Return artifact
              ▼
         ┌──────────┐
         │  Client  │
         └──────────┘
```

## Tools Architecture

```
BaseTool (Abstract)
    │
    ├─ execute(**kwargs) → Dict[str, Any]
    │
    ├─ ExtractCodeTool
    │   └─ Extract code from artifact
    │
    ├─ UpdateCodeBlockTool
    │   └─ Update specific line range
    │
    ├─ ConvertArtifactTypeTool
    │   └─ Convert code ↔ text
    │
    └─ AnalyzeArtifactTool
        └─ Get metrics and insights
```

## Error Handling

```
Try:
    Process Request
    ├─ Detect intent
    ├─ Route to agent
    ├─ Generate artifact
    └─ Stream events
    
Catch Exception:
    │
    ▼
Emit RUN_ERROR Event
    ├─ type: "run_error"
    ├─ thread_id: "..."
    ├─ run_id: "..."
    └─ message: "Error details"
    │
    ▼
Return Error Stream
```

## Legend

```
┌────┐
│    │  Component
└────┘

  │
  ▼    Data flow

  →    Process flow

 ├──   Branch/Option

[...]  Conditional
```
