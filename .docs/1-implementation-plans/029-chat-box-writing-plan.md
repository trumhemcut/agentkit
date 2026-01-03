# 029 - Chat Box Writing (Stop Agent) Implementation Plan

## Overview

**Requirement**: When agent is streaming a response, the Send button should transform into a Stop button (similar to Gemini's UI). Clicking Stop should abort the agent stream. Additionally, users should be able to type new messages during streaming, and pressing Enter should stop the current stream and send the new message.

**Reference**: `.docs/0-requirements/029-chat-box-writing.md`, `.docs/0-requirements/images/gemini-writing.png`

**Goal**: Improve user control over agent conversations by allowing interruption of long responses.

---

## Architecture Overview

### Current State Analysis

**Frontend**:
- `ChatInput.tsx` - Has Send button, currently disabled during streaming
- `ChatContainer.tsx` - Manages `isSending` state, controls input disabled state
- `services/api.ts` - Uses fetch API for streaming, but no abort capability

**Backend**:
- `api/routes.py` - Streams AG-UI events via FastAPI StreamingResponse
- LangGraph agents stream chunks asynchronously
- No built-in cancellation mechanism currently

### Key Changes Required

1. **Frontend**: Transform Send button to Stop button based on streaming state
2. **Frontend**: Enable input field during streaming
3. **Frontend**: Add AbortController to cancel fetch requests
4. **Frontend**: Handle Enter key during streaming to stop and send new message
5. **Backend**: Handle client disconnection gracefully (FastAPI already supports this)

---

## 1. Backend Tasks (Minimal Changes)

### Task 1.1: Verify Graceful Disconnection Handling

**File**: `backend/api/routes.py`

**Analysis**: FastAPI's StreamingResponse already handles client disconnections gracefully. When client aborts, the generator stops naturally.

**Action**: Add diagnostic logging to detect disconnections:

```python
async def event_generator():
    try:
        # ... existing streaming logic ...
        async for event in graph.astream(state):
            yield encoder.encode(event)
    except GeneratorExit:
        logger.info(f"[ROUTES] Client disconnected for run_id={input_data.run_id}")
        # Cleanup if needed
    except Exception as e:
        logger.error(f"[ROUTES] Error in event generator: {e}")
        yield encoder.encode(RunErrorEvent(...))
```

**Verification**: Test that agent stops streaming when frontend aborts request.

---

### Task 1.2: Add Cancellation Support to LangGraph (Optional Enhancement)

**Files**: ALL graph files in `backend/graphs/`:
- `chat_graph.py`
- `canvas_graph.py`
- `a2ui_graph.py`
- `a2ui_loop_graph.py`
- `insurance_supervisor_graph.py`
- `salary_viewer_graph.py`
- `graph_factory.py` (coordination)

**Purpose**: For future enhancement to actively cancel LLM streaming when client disconnects. This applies to **ALL graphs** in the system.

**Implementation Strategy** (Optional for Phase 2):

**Option 1: Centralized Approach in graph_factory.py**

```python
# In graph_factory.py
from langgraph.pregel import Pregel
from typing import Optional

def add_cancellation_support(graph: Pregel, run_id: str) -> Pregel:
    """
    Add cancellation support to any graph.
    This wrapper applies to all graph types uniformly.
    """
    graph = graph.with_config(
        {
            "configurable": {
                "run_id": run_id,
                "checkpoint_ns": f"run_{run_id}"
            },
            "recursion_limit": 50
        }
    )
    return graph

# Update graph_factory to apply cancellation to all graphs
class GraphFactory:
    def get_graph(self, agent_id: str, model: Optional[str] = None, run_id: Optional[str] = None):
        """Get graph instance with optional cancellation support"""
        
        if agent_id == "chat":
            graph = create_chat_graph(model)
        elif agent_id == "canvas":
            graph = create_canvas_graph(model)
        elif agent_id == "a2ui":
            graph = create_a2ui_graph(model)
        elif agent_id == "a2ui-loop":
            graph = create_a2ui_loop_graph(model)
        elif agent_id == "insurance-supervisor":
            graph = create_insurance_supervisor_graph(model)
        elif agent_id == "salary-viewer":
            graph = create_salary_viewer_graph(model)
        else:
            raise ValueError(f"Unknown agent_id: {agent_id}")
        
        # Apply cancellation support if run_id provided
        if run_id:
            graph = add_cancellation_support(graph, run_id)
        
        return graph
```

**Option 2: Individual Graph Updates**

Each graph file adds cancellation support:

```python
# Example: In chat_graph.py, canvas_graph.py, a2ui_graph.py, etc.
def create_xxx_graph(model: str = None, run_id: str = None):
    # ... existing graph construction ...
    
    if run_id:
        graph = graph.with_config({
            "configurable": {
                "run_id": run_id,
                "checkpoint_ns": f"run_{run_id}"
            }
        })
    
    return graph
```

**Files to Update**:
1. ✅ `graphs/chat_graph.py`
2. ✅ `graphs/canvas_graph.py`
3. ✅ `graphs/a2ui_graph.py`
4. ✅ `graphs/a2ui_loop_graph.py`
5. ✅ `graphs/insurance_supervisor_graph.py`
6. ✅ `graphs/salary_viewer_graph.py`
7. ✅ `graphs/graph_factory.py` (if using centralized approach)

**Recommendation**: Use **Option 1 (Centralized)** for consistency and easier maintenance across all graph types.

**Note**: This is optional as FastAPI already handles disconnection. LangGraph will naturally stop when the async generator is closed. However, adding explicit cancellation support allows for:
- Active cleanup of LLM streaming requests
- Better resource management
- Potential cost savings on expensive model calls
- Consistent cancellation behavior across all agent types

---

## 2. AG-UI Protocol (No Changes Required)

### Protocol Analysis

**Current Events**:
- `RUN_STARTED` - Indicates streaming started
- `TEXT_MESSAGE_START` - New message begins
- `TEXT_MESSAGE_CONTENT` - Streaming chunks
- `TEXT_MESSAGE_END` - Message complete
- `RUN_FINISHED` - Stream complete
- `RUN_ERROR` - Error occurred

**Cancellation Flow**:
1. Frontend calls `abortController.abort()`
2. Fetch request is cancelled
3. Backend detects disconnection
4. Backend stops streaming naturally
5. Frontend cleans up state

**No new events needed** - client-side cancellation is transparent to protocol.

---

## 3. Frontend Tasks (Primary Implementation)

### Task 3.1: Add AbortController Support to API Service

**File**: `frontend/services/api.ts`

**Changes**:

1. Update `sendChatMessage` signature to return AbortController:

```typescript
export async function sendChatMessage(
  messages: Message[],
  threadId: string,
  runId: string,
  model: string | undefined,
  provider: string | undefined,
  agent: string | undefined,
  onEvent: (event: any) => void
): Promise<AbortController> {
  const abortController = new AbortController();
  
  try {
    const chatRequest: ChatRequest = {
      thread_id: threadId,
      run_id: runId,
      messages: messages,
      model: model,
      provider: provider,
      agent: agent || 'chat',
    };

    const response = await fetch(`${API_BASE_URL}/api/chat/${agent || 'chat'}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
      },
      body: JSON.stringify(chatRequest),
      signal: abortController.signal, // 🔑 Add abort signal
    });

    // ... rest of streaming logic ...
    
  } catch (error) {
    // Handle abort specifically
    if (error instanceof DOMException && error.name === 'AbortError') {
      console.log('[API] Request aborted by user');
      onEvent({
        type: 'STREAM_ABORTED',
        message: 'Request cancelled by user',
        timestamp: Date.now(),
      });
      return abortController;
    }
    
    // Handle other errors
    console.error('[API] Error sending chat message:', error);
    onEvent({
      type: 'ERROR',
      message: error instanceof Error ? error.message : 'Unknown error',
      timestamp: Date.now(),
    });
  }
  
  return abortController;
}
```

2. Similarly update `sendCanvasMessage` with AbortController support.

---

### Task 3.2: Update ChatContainer to Store AbortController

**File**: `frontend/components/ChatContainer.tsx`

**Changes**:

1. Add ref to store current AbortController:

```typescript
export const ChatContainer = forwardRef<ChatContainerRef, ChatContainerProps>(
  function ChatContainer({ /* ... */ }, ref) {
    // ... existing state ...
    
    // 🔑 Add abort controller ref
    const currentAbortControllerRef = useRef<AbortController | null>(null);
    
    // ... rest of component ...
```

2. Update `handleSendMessage` to store controller:

```typescript
const handleSendMessage = async (content: string) => {
  if (!threadId) return;
  
  // 🔑 Check if already streaming - if so, stop first
  if (isSending && currentAbortControllerRef.current) {
    console.log('[ChatContainer] Stopping current stream before sending new message');
    currentAbortControllerRef.current.abort();
    currentAbortControllerRef.current = null;
    
    // Wait a brief moment for cleanup
    await new Promise(resolve => setTimeout(resolve, 100));
  }
  
  if (!selectedAgent) {
    console.error('Cannot send message: Agent not loaded yet');
    return;
  }

  setIsSending(true);
  
  // ... create user message and add to chat ...
  
  try {
    const client = getClient();
    
    // 🔑 Store abort controller
    if (selectedAgent === 'canvas' && canvasContext?.artifact) {
      currentAbortControllerRef.current = await sendCanvasMessage(
        apiMessages,
        threadId,
        runId,
        selectedModel,
        selectedProvider,
        canvasContext.artifact,
        canvasContext.artifactId,
        selectedTextData,
        (event) => processEvent(event)
      );
    } else {
      currentAbortControllerRef.current = await sendChatMessage(
        apiMessages,
        threadId,
        runId,
        selectedModel,
        selectedProvider,
        selectedAgent,
        (event) => processEvent(event)
      );
    }
    
  } catch (error) {
    console.error('Error sending message:', error);
    setIsSending(false);
    setConnectionState(false, error instanceof Error ? error.message : 'Unknown error');
  }
};
```

3. Add stop handler function:

```typescript
const handleStopStreaming = () => {
  console.log('[ChatContainer] User requested stop streaming');
  
  if (currentAbortControllerRef.current) {
    currentAbortControllerRef.current.abort();
    currentAbortControllerRef.current = null;
    setIsSending(false);
    
    // Update the current agent message to mark it as interrupted
    const currentMsg = currentAgentMessageRef.current;
    if (currentMsg && currentMsg.isStreaming) {
      const interruptedMessage = {
        ...currentMsg,
        isStreaming: false,
        content: currentMsg.content + '\n\n_[Response interrupted by user]_'
      };
      updateMessage(interruptedMessage.id, interruptedMessage);
      currentAgentMessageRef.current = null;
    }
  }
};
```

4. Update RUN_FINISHED handler to clear abort controller:

```typescript
const unsubscribeFinish = on(EventType.RUN_FINISHED, (event) => {
  console.log('[ChatContainer] Agent run finished:', event);
  setIsSending(false);
  currentAbortControllerRef.current = null; // 🔑 Clear controller
  
  // ... existing logic ...
});
```

5. Pass stop handler to ChatInput:

```typescript
<ChatInput 
  ref={chatInputRef}
  onSendMessage={handleSendMessage}
  onStopStreaming={handleStopStreaming} // 🔑 New prop
  disabled={!isConnected}
  isStreaming={isSending} // 🔑 New prop
  placeholder={/* ... */}
/>
```

---

### Task 3.3: Transform ChatInput Send Button to Stop Button

**File**: `frontend/components/ChatInput.tsx`

**Changes**:

1. Update component interface:

```typescript
interface ChatInputProps {
  onSendMessage: (message: string) => void;
  onStopStreaming?: () => void; // 🔑 New callback
  disabled?: boolean;
  isStreaming?: boolean; // 🔑 New prop to track streaming state
  placeholder?: string;
}
```

2. Add Stop icon import:

```typescript
import { Send, Plus, Wrench, Upload, Image, Code, FileText, Square } from 'lucide-react';
// Square icon will be used as Stop button
```

3. Update button logic:

```typescript
export const ChatInput = forwardRef<ChatInputRef, ChatInputProps>(function ChatInput({ 
  onSendMessage,
  onStopStreaming,
  disabled = false,
  isStreaming = false, // 🔑 Track streaming state
  placeholder = "Type your message..."
}, ref) {
  const [message, setMessage] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const isMobile = useIsMobile();

  // ... existing code ...

  const handleSend = () => {
    const trimmedMessage = message.trim();
    if (trimmedMessage && !disabled) {
      onSendMessage(trimmedMessage);
      setMessage('');
    }
  };
  
  // 🔑 New handler for stop button
  const handleStop = () => {
    if (onStopStreaming) {
      onStopStreaming();
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      
      // 🔑 If streaming, stop and send new message
      if (isStreaming) {
        handleStop();
        // Wait briefly then send
        setTimeout(() => handleSend(), 150);
      } else {
        handleSend();
      }
    }
  };

  // ... rest of component ...
```

4. Update Send/Stop button rendering:

```typescript
{/* Send/Stop Button */}
{isStreaming ? (
  // 🔑 Stop button when streaming
  <TooltipProvider>
    <Tooltip>
      <TooltipTrigger asChild>
        <Button
          onClick={handleStop}
          disabled={disabled}
          size="icon"
          variant="destructive" // Red color for stop action
          className={cn(
            "shrink-0",
            isMobile ? "h-8 w-8" : "h-9 w-9"
          )}
        >
          <Square className={isMobile ? "h-4 w-4" : "h-5 w-5"} fill="currentColor" />
        </Button>
      </TooltipTrigger>
      <TooltipContent>
        <p>Stop generating</p>
      </TooltipContent>
    </Tooltip>
  </TooltipProvider>
) : (
  // 🔑 Send button when not streaming
  <TooltipProvider>
    <Tooltip>
      <TooltipTrigger asChild>
        <Button
          onClick={handleSend}
          disabled={disabled || !message.trim()}
          size="icon"
          className={cn(
            "shrink-0",
            isMobile ? "h-8 w-8" : "h-9 w-9"
          )}
        >
          <Send className={isMobile ? "h-4 w-4" : "h-5 w-5"} />
        </Button>
      </TooltipTrigger>
      <TooltipContent>
        <p>Send message</p>
      </TooltipContent>
    </Tooltip>
  </TooltipProvider>
)}
```

5. Update textarea disabled logic:

```typescript
<Textarea
  ref={textareaRef}
  value={message}
  onChange={(e) => setMessage(e.target.value)}
  onKeyDown={handleKeyDown}
  placeholder={placeholder}
  disabled={disabled} // 🔑 Remove isStreaming from disabled condition
  className={cn(
    "resize-none w-full pr-3 rounded-3xl shadow-md hover:shadow-lg transition-shadow",
    isMobile ? "min-h-[50px] max-h-[85px] pb-11 pl-3 pt-3" : "min-h-[60px] max-h-[120px] pb-11 pl-4 pt-3"
  )}
  rows={isMobile ? 1 : 2}
/>
```

6. Update hint text:

```typescript
<p className={cn(
  "mt-2 text-muted-foreground",
  isMobile ? "text-[10px]" : "text-xs"
)}>
  {isStreaming 
    ? "Press Enter to stop and send new message" // 🔑 Dynamic hint
    : "Press Enter to send, Shift+Enter for new line"
  }
</p>
```

---

### Task 3.4: Update TypeScript Types

**File**: `frontend/types/agui.ts` (if needed)

Add new event type for stream abortion (optional):

```typescript
export enum EventType {
  // ... existing events ...
  STREAM_ABORTED = 'STREAM_ABORTED', // 🔑 New type
}
```

---

## 4. Testing & Verification

### Manual Testing Checklist

**Test 1: Stop Button Appears During Streaming**
- [ ] Send a message that triggers long response
- [ ] Verify Send button transforms to Stop button (red, square icon)
- [ ] Verify tooltip shows "Stop generating"

**Test 2: Stop Button Functionality**
- [ ] Click Stop button during streaming
- [ ] Verify stream stops immediately
- [ ] Verify message shows "[Response interrupted by user]" indicator
- [ ] Verify Stop button returns to Send button
- [ ] Verify input field is re-enabled

**Test 3: Type and Send During Streaming**
- [ ] Start streaming a response
- [ ] Type a new message in the input field
- [ ] Press Enter
- [ ] Verify previous stream stops
- [ ] Verify new message is sent
- [ ] Verify new stream starts

**Test 4: Error Handling**
- [ ] Test with network disconnection during streaming
- [ ] Test with backend error during streaming
- [ ] Verify graceful error messages

**Test 5: Mobile Responsiveness**
- [ ] Test Stop button on mobile viewport
- [ ] Verify button size and touch target are appropriate
- [ ] Verify hint text updates correctly

**Test 6: Canvas Mode**
- [ ] Test stop functionality in Canvas mode
- [ ] Verify artifact updates stop when interrupted
- [ ] Verify state remains consistent

---

## 5. Implementation Order

### Phase 1: Core Stop Functionality (Priority 1)
1. Task 3.1: Add AbortController to API service ✅
2. Task 3.2: Update ChatContainer with abort logic ✅
3. Task 3.3: Transform Send to Stop button ✅
4. Testing: Basic stop functionality

### Phase 2: Enhanced UX (Priority 2)
5. Task 3.3 (continued): Enable typing during streaming ✅
6. Task 3.3 (continued): Handle Enter key during streaming ✅
7. Task 1.1: Add backend disconnection logging
8. Testing: Complete UX flow

### Phase 3: Polish (Priority 3)
9. Visual polish: Button transition animations
10. Accessibility: ARIA labels and keyboard navigation
11. Documentation: Update knowledge base

---

## 6. Edge Cases & Considerations

### Edge Case 1: Multiple Rapid Stops
**Problem**: User clicks Stop multiple times rapidly  
**Solution**: Disable Stop button immediately after first click, clear controller

### Edge Case 2: Stop During Artifact Generation
**Problem**: Canvas artifacts may be partially generated  
**Solution**: Update artifact cache to mark as incomplete, show indicator

### Edge Case 3: Network Latency
**Problem**: Stop command may not reach server immediately  
**Solution**: Frontend shows immediate UI feedback, backend handles naturally

### Edge Case 4: Backend Still Processing
**Problem**: LLM may still be generating tokens when disconnected  
**Solution**: FastAPI/LangGraph will clean up automatically when generator is closed

---

## 7. Success Metrics

- Users can stop agent streaming by clicking Stop button
- Users can type new messages during streaming
- Pressing Enter during streaming stops and sends new message
- UI provides clear visual feedback (Send ↔ Stop transformation)
- No memory leaks or dangling requests
- Graceful error handling when network issues occur

---

## 8. Future Enhancements

### Phase 4 (Optional):
- Add "Continue generating" button after stop
- Show token count / cost when stopped
- Add keyboard shortcut (Esc) to stop
- Add warning before stopping long-running expensive operations
- Backend: Active LLM cancellation (currently passive)

---

## Dependencies

**Frontend**:
- Shadcn UI Button, Tooltip components
- Lucide React icons (Square for Stop)
- AbortController API (native browser API)

**Backend**:
- FastAPI StreamingResponse (existing)
- LangGraph async generators (existing)

**No new dependencies required** ✅

---

## Notes for Implementation Agents

**Backend Agent**:
- Focus on Task 1.1 (logging)
- Verify existing graceful disconnection works
- Test LangGraph behavior on client disconnect

**Frontend Agent**:
- Focus on Tasks 3.1, 3.2, 3.3 (core UI transformation)
- Follow Shadcn UI patterns for button variants
- Ensure TypeScript types are correct
- Test thoroughly with different streaming scenarios

**Key Pattern**: This feature leverages browser's native AbortController and FastAPI's natural disconnection handling - minimal backend changes needed. Primary work is frontend UX transformation.
