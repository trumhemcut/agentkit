# Canvas Feature - Frontend Implementation Summary

## Overview
The Canvas feature provides a split-view interface where users can chat with AI agents on the left to create and edit artifacts (code/text) displayed on the right.

## Architecture

### 1. Type Definitions ([types/canvas.ts](../types/canvas.ts))
- `ArtifactContentCode` - Code artifact with syntax highlighting
- `ArtifactContentText` - Text artifact with markdown support
- `ArtifactV3` - Artifact container with versioning
- `CanvasMessage` - Message format for canvas API

### 2. Context Management ([contexts/CanvasContext.tsx](../contexts/CanvasContext.tsx))
Manages canvas state including:
- Current artifact and version
- Streaming state
- Content updates
- Version navigation

### 3. Core Components

#### Resizable Divider ([components/ResizableDivider.tsx](../../frontend/components/ResizableDivider.tsx))
Draggable vertical divider for adjusting panel widths:
- Minimum width: 20% (configurable)
- Maximum width: 70% (configurable)
- Default: 33.33% (1:2 ratio)
- Visual grip indicator on hover
- Smooth drag interaction with cursor feedback

#### Canvas Layout ([components/Canvas/CanvasLayout.tsx](../components/Canvas/CanvasLayout.tsx))
Split-view layout with adjustable ratio:
- Left: Chat panel (resizable from 20% to 70%)
- Center: Resizable divider
- Right: Artifact panel (automatically sized)
- Layout persists during session

#### Artifact Renderer ([components/Canvas/ArtifactRenderer.tsx](../components/Canvas/ArtifactRenderer.tsx))
Main component for displaying artifacts:
- Switches between CodeRenderer and TextRenderer
- Handles version navigation
- Provides copy/download actions
- Shows empty state when no artifact exists

#### Code Renderer ([components/Canvas/CodeRenderer.tsx](../components/Canvas/CodeRenderer.tsx))
Code editor with syntax highlighting using CodeMirror:
- Supports: JavaScript, TypeScript, Python, HTML, CSS, JSON
- Shows streaming indicator during generation
- Editable after generation completes

#### Text Renderer ([components/Canvas/TextRenderer.tsx](../components/Canvas/TextRenderer.tsx))
Rich markdown editor using BlockNote:
- WYSIWYG markdown editing
- Shows streaming indicator during generation
- Editable after generation completes

#### Artifact Header ([components/Canvas/ArtifactHeader.tsx](../components/Canvas/ArtifactHeader.tsx))
Header with controls:
- Artifact title
- Version navigation (previous/next)
- Copy to clipboard
- Download file

#### Canvas Chat Container ([components/Canvas/CanvasChatContainer.tsx](../components/Canvas/CanvasChatContainer.tsx))
Specialized chat component for canvas mode:
- Sends artifact state with each message
- Handles canvas-specific AG-UI events
- Displays chat history

### 4. AG-UI Integration

#### Client Extensions ([services/agui-client.ts](../services/agui-client.ts))
Extended AG-UI client with canvas event handlers:
- `artifact_created` - New artifact created
- `artifact_streaming_start` - Artifact generation begins
- `artifact_streaming` - Streaming content delta
- `artifact_updated` - Artifact update complete
- `artifact_version_changed` - Version navigation

#### API Service ([services/api.ts](../services/api.ts))
Canvas-specific API function:
- `sendCanvasMessage()` - Sends message with artifact context
- Handles SSE streaming from backend
- Processes canvas AG-UI events

### 5. Canvas Page ([app/canvas/page.tsx](../app/canvas/page.tsx))
Main canvas application page:
- Wraps everything in CanvasProvider
- Sets up canvas event handlers
- Connects chat and artifact panels

## Usage

### Access Canvas Mode
Navigate to `/canvas` route

### Create Artifact
Chat with the AI agent:
- "Create a Python script that..."
- "Write a React component for..."
- "Generate markdown documentation about..."

### Edit Artifact
With existing artifact:
- "Update the function to..."
- "Add error handling to..."
- "Rewrite this as..."

### Version Navigation
- Use arrow buttons in artifact header
- Navigate between different versions
- Each version preserves full content

## Event Flow

1. **User sends message** → CanvasChatContainer
2. **Message sent to backend** → sendCanvasMessage()
3. **Backend processes** → Canvas graph & agent
4. **Events streamed back** → AG-UI client
5. **Canvas events handled** → CanvasContext updates
6. **UI updates** → ArtifactRenderer shows changes

## Key Features

✅ Split-view layout (chat + artifact)
✅ Syntax-highlighted code editing
✅ Rich markdown editing
✅ Real-time streaming generation
✅ Version history navigation
✅ Copy/download artifacts
✅ Empty state guidance

## Dependencies

- **@uiw/react-codemirror** - Code editor
- **@codemirror/lang-*** - Language support
- **@blocknote/core** - Block editor core
- **@blocknote/react** - React bindings
- **@blocknote/shadcn** - Shadcn UI styling
- **uuid** - ID generation

## Next Steps / Future Enhancements

- Add resizable panels (react-resizable-panels or custom implementation)
- Text selection for inline editing
- Multiple artifacts per thread
- Artifact persistence to backend
- Collaborative editing
- Export to various formats
- Code execution preview

## Related Files

- Backend: `backend/agents/canvas_agent.py`
- Backend: `backend/graphs/canvas_graph.py`
- Backend: `backend/api/routes.py` (canvas endpoints)
- Implementation Plan: `.docs/1-implementation-plans/canvas-feature.md`
