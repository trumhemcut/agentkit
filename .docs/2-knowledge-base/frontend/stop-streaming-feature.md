# Stop Streaming Feature

## Overview

The Stop Streaming feature allows users to interrupt agent responses during streaming, similar to modern chat interfaces like Gemini. When an agent is responding, the Send button transforms into a Stop button (red with square icon), and users can continue typing while streaming is active.

**Implementation Date**: January 3, 2026  
**Related Plan**: `.docs/1-implementation-plans/029-chat-box-writing-plan.md`

---

## Key Features

1. **Send → Stop Button Transformation**: During streaming, the Send button becomes a red Stop button with a square icon
2. **Active Typing During Streaming**: Input field remains enabled while agent is responding
3. **Enter Key Interrupt**: Pressing Enter during streaming stops the current response and sends the new message
4. **Abort Controller**: Uses browser's native AbortController API for clean request cancellation
5. **Visual Feedback**: Interrupted messages show "[Response interrupted by user]" indicator

---

## Architecture

### Frontend Components

#### 1. API Service (`frontend/services/api.ts`)

**Changes Made**:
- Both `sendChatMessage()` and `sendCanvasMessage()` now return `AbortController`
- Each function creates an `AbortController` and passes its signal to the fetch request
- Handles `AbortError` specifically to emit `STREAM_ABORTED` event
- Returns the controller for external management

**Key Pattern**:
```typescript
export async function sendChatMessage(
  // ... parameters
): Promise<AbortController> {
  const abortController = new AbortController();
  
  const response = await fetch(url, {
    signal: abortController.signal, // Add abort signal
    // ... other options
  });
  
  // Handle abort specifically
  catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      console.log('[API] Request aborted by user');
      onEvent({ type: 'STREAM_ABORTED', message: 'Request cancelled by user' });
      return abortController;
    }
  }
  
  return abortController;
}
```

#### 2. ChatContainer (`frontend/components/ChatContainer.tsx`)

**Changes Made**:
- Added `currentAbortControllerRef` to store active abort controller
- Implemented `handleStopStreaming()` function to abort requests and update UI
- Modified `handleSendMessage()` to:
  - Check if already streaming and stop first if needed
  - Store the abort controller returned from API calls
- Updated `RUN_FINISHED` handler to clear abort controller
- Added new props to `ChatInput`: `onStopStreaming` and `isStreaming`

**Key Pattern**:
```typescript
// Store abort controller ref
const currentAbortControllerRef = useRef<AbortController | null>(null);

// Stop handler
const handleStopStreaming = () => {
  if (currentAbortControllerRef.current) {
    currentAbortControllerRef.current.abort();
    currentAbortControllerRef.current = null;
    setIsSending(false);
    
    // Mark message as interrupted
    const currentMsg = currentAgentMessageRef.current;
    if (currentMsg && currentMsg.isStreaming) {
      updateMessage(currentMsg.id, {
        ...currentMsg,
        isStreaming: false,
        content: currentMsg.content + '\n\n_[Response interrupted by user]_'
      });
    }
  }
};

// Send handler checks for existing stream
const handleSendMessage = async (content: string) => {
  // If already streaming, stop first
  if (isSending && currentAbortControllerRef.current) {
    currentAbortControllerRef.current.abort();
    currentAbortControllerRef.current = null;
    await new Promise(resolve => setTimeout(resolve, 100));
  }
  
  // Store new abort controller
  currentAbortControllerRef.current = await sendChatMessage(...);
};
```

#### 3. ChatInput (`frontend/components/ChatInput.tsx`)

**Changes Made**:
- Added `Square` icon import from lucide-react
- Updated `ChatInputProps` interface with:
  - `onStopStreaming?: () => void`
  - `isStreaming?: boolean`
- Added `handleStop()` function
- Modified `handleKeyDown()` to handle Enter key during streaming
- Replaced Send button with conditional rendering (Send vs Stop)
- Updated hint text to be dynamic based on streaming state

**Key Pattern**:
```typescript
interface ChatInputProps {
  onSendMessage: (message: string) => void;
  onStopStreaming?: () => void;
  disabled?: boolean;
  isStreaming?: boolean;
  placeholder?: string;
}

// Handle Enter key
const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    
    // If streaming, stop and send new message
    if (isStreaming) {
      handleStop();
      setTimeout(() => handleSend(), 150);
    } else {
      handleSend();
    }
  }
};

// Conditional button rendering
{isStreaming ? (
  <Button variant="destructive" onClick={handleStop}>
    <Square fill="currentColor" />
  </Button>
) : (
  <Button onClick={handleSend} disabled={disabled || !message.trim()}>
    <Send />
  </Button>
)}

// Dynamic hint
{isStreaming 
  ? "Press Enter to stop and send new message" 
  : "Press Enter to send, Shift+Enter for new line"
}
```

#### 4. Type Definitions (`frontend/types/agui.ts`)

**Changes Made**:
- Added `STREAM_ABORTED` to `EventType` enum
- Created `StreamAbortedEvent` interface

```typescript
export enum EventType {
  // ... other events
  STREAM_ABORTED = 'STREAM_ABORTED',
  // ...
}

export interface StreamAbortedEvent extends BaseEvent {
  type: EventType.STREAM_ABORTED;
  message?: string;
}
```

---

## User Experience Flow

### Normal Flow (Streaming → Complete)
1. User sends message
2. Send button becomes Stop button (red, square icon)
3. Input field remains enabled (user can type)
4. Agent streams response chunks
5. Stream completes naturally
6. Stop button returns to Send button

### Interrupted Flow (User Stops)
1. User sends message
2. Send button becomes Stop button
3. Agent starts streaming
4. **User clicks Stop button OR types new message + Enter**
5. Request is aborted via `AbortController`
6. Current message marked with "[Response interrupted by user]"
7. If Enter was pressed: new message is sent after brief delay
8. Stop button returns to Send button

---

## Backend Considerations

The backend requires **no changes** for basic functionality:
- FastAPI's `StreamingResponse` handles client disconnection gracefully
- LangGraph generators stop naturally when client disconnects
- The async generator is closed automatically when fetch is aborted

**Optional Enhancement** (not implemented yet):
- Add explicit cancellation to LangGraph graphs for active LLM stream termination
- See implementation plan for details on LangGraph cancellation support

---

## Testing Checklist

- [x] Stop button appears during streaming
- [x] Stop button has correct styling (red, square icon, tooltip)
- [x] Clicking Stop button cancels stream immediately
- [x] Input field remains enabled during streaming
- [x] User can type new message during streaming
- [x] Pressing Enter during streaming stops and sends new message
- [x] Interrupted messages show indicator
- [x] No memory leaks (abort controller is cleaned up)
- [x] Works in both chat and canvas modes
- [x] Mobile responsive (button sizes, touch targets)

---

## Dependencies

- **Browser**: Native `AbortController` API (modern browsers)
- **Icons**: `lucide-react` - Square icon for Stop button
- **UI**: Shadcn UI Button, Tooltip components
- **No new packages required**

---

## Known Limitations

1. **Backend LLM Streaming**: The backend may continue processing tokens briefly after abort (LLM calls are not actively cancelled, just the HTTP stream is closed)
2. **Network Latency**: Stop command UI feedback is immediate, but backend receives notification asynchronously
3. **Canvas Artifacts**: Partial artifacts are kept in current state (not rolled back)

---

## Future Enhancements

### Potential Improvements:
1. **Continue Generation**: Add button to resume from where stopped
2. **Token Counter**: Show tokens consumed when stopped
3. **Keyboard Shortcut**: Add Esc key to stop streaming
4. **Cost Warning**: Warn before stopping expensive operations
5. **Active LLM Cancellation**: Implement backend-side LLM stream cancellation

### Backend Enhancement (Optional):
Implement active LangGraph cancellation:
```python
# In graph creation
graph = graph.with_config({
    "configurable": {
        "run_id": run_id,
        "checkpoint_ns": f"run_{run_id}"
    }
})
```

---

## Related Files

### Frontend:
- `/frontend/services/api.ts` - API client with AbortController
- `/frontend/components/ChatContainer.tsx` - State management and handlers
- `/frontend/components/ChatInput.tsx` - UI transformation
- `/frontend/types/agui.ts` - Event type definitions

### Documentation:
- `/.docs/1-implementation-plans/029-chat-box-writing-plan.md` - Original plan
- `/.docs/0-requirements/029-chat-box-writing.md` - Requirements

---

## Key Takeaways

1. **Browser AbortController is powerful**: Native API handles request cancellation cleanly
2. **FastAPI naturally handles disconnection**: No backend changes needed for basic functionality
3. **UI state management is critical**: Must sync abort controller with streaming state
4. **User experience matters**: Keeping input enabled + dynamic hints improves UX
5. **Type safety**: TypeScript interfaces ensure correct prop passing throughout component tree

---

## Pattern: Stop Streaming in Other Agents

To implement similar stop functionality in other agent types:

1. Ensure API call returns `AbortController`
2. Store controller in component ref
3. Create stop handler that calls `abort()`
4. Pass `isStreaming` and `onStopStreaming` to input component
5. Clear controller on stream completion
6. Handle Enter key appropriately

This pattern can be reused for any streaming agent interaction.
