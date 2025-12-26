# Implementation Plan: Auto-scroll Chat Messages

**Requirement**: [014-fe-autoscroll.md](../0-requirements/014-fe-autoscroll.md)  
**Type**: Frontend Only  
**Priority**: Medium  
**Estimated Effort**: 2-3 hours

## Problem Statement

Currently, the chat scrollbar does not automatically scroll to the bottom when new messages arrive from the user or agent. This creates a poor UX as users must manually scroll to see new content.

**Requirements**:
- ✅ Auto-scroll when user sends a message
- ✅ Auto-scroll when agent responds (streaming or complete)
- ❌ Do NOT auto-scroll on initial thread history load
- ✅ Preserve user's scroll position if they've manually scrolled up

## Technical Analysis

### Components Involved

1. **ChatContainer** (`/frontend/components/ChatContainer.tsx`)
   - Main container managing chat display
   - Handles message rendering and scroll behavior

2. **MessageHistory** (`/frontend/components/MessageHistory.tsx`)
   - Renders message list
   - Manages scroll container reference

3. **useMessages** (`/frontend/hooks/useMessages.ts`)
   - Manages message state
   - Handles new message additions

4. **useAGUI** (`/frontend/hooks/useAGUI.ts`)
   - Handles streaming events from backend
   - Processes TEXT_MESSAGE_CHUNK events

### Scroll Behavior Logic

Need to implement:
- **Scroll State Tracking**: Detect if user has manually scrolled up
- **Auto-scroll Trigger**: Scroll on new message only if user is near bottom
- **Scroll Prevention**: Skip auto-scroll on initial history load

## Implementation Steps

### Step 1: Add Scroll State Management Hook
**File**: `/frontend/hooks/useAutoScroll.ts` (NEW)

Create a custom hook to manage auto-scroll behavior:

```typescript
import { useRef, useEffect, useState } from 'react';

export const useAutoScroll = (dependencies: any[]) => {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [shouldAutoScroll, setShouldAutoScroll] = useState(true);
  const [isInitialLoad, setIsInitialLoad] = useState(true);
  const isUserScrollingRef = useRef(false);

  // Detect user manual scroll
  const handleScroll = () => {
    if (!scrollRef.current) return;
    
    const { scrollTop, scrollHeight, clientHeight } = scrollRef.current;
    const distanceFromBottom = scrollHeight - scrollTop - clientHeight;
    
    // Consider "at bottom" if within 100px
    const isAtBottom = distanceFromBottom < 100;
    setShouldAutoScroll(isAtBottom);
  };

  // Scroll to bottom
  const scrollToBottom = (smooth = true) => {
    if (!scrollRef.current) return;
    
    scrollRef.current.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: smooth ? 'smooth' : 'auto'
    });
  };

  // Auto-scroll on new messages
  useEffect(() => {
    if (isInitialLoad) {
      // Skip auto-scroll on first load
      setIsInitialLoad(false);
      return;
    }

    if (shouldAutoScroll) {
      scrollToBottom();
    }
  }, dependencies);

  return {
    scrollRef,
    handleScroll,
    scrollToBottom,
    shouldAutoScroll
  };
};
```

### Step 2: Update MessageHistory Component
**File**: `/frontend/components/MessageHistory.tsx`

Integrate auto-scroll hook:

```typescript
import { useAutoScroll } from '@/hooks/useAutoScroll';

export const MessageHistory = ({ messages, ...props }) => {
  const { scrollRef, handleScroll } = useAutoScroll([messages]);

  return (
    <div 
      ref={scrollRef}
      onScroll={handleScroll}
      className="flex-1 overflow-y-auto"
    >
      {/* Render messages */}
    </div>
  );
};
```

### Step 3: Handle Streaming Message Updates
**File**: `/frontend/hooks/useAGUI.ts`

Ensure streaming chunks trigger scroll:

```typescript
// When processing TEXT_MESSAGE_CHUNK events
case 'TEXT_MESSAGE_CHUNK':
  // Update message content
  updateStreamingMessage(event.data);
  // This should trigger auto-scroll via useAutoScroll hook
  break;
```

### Step 4: Handle Thread Switching
**File**: `/frontend/hooks/useChatThreads.ts`

Mark initial load when switching threads:

```typescript
const switchThread = (threadId: string) => {
  // Load thread messages
  const messages = loadMessagesForThread(threadId);
  
  // Signal initial load (no auto-scroll)
  setIsInitialLoad(true);
  
  setMessages(messages);
};
```

### Step 5: Add Scroll-to-Bottom Button (Optional Enhancement)
**File**: `/frontend/components/ScrollToBottomButton.tsx` (NEW)

Add a floating button that appears when user scrolls up:

```typescript
export const ScrollToBottomButton = ({ 
  visible, 
  onClick 
}: { 
  visible: boolean; 
  onClick: () => void 
}) => {
  if (!visible) return null;

  return (
    <button
      onClick={onClick}
      className="absolute bottom-4 right-4 bg-primary text-white rounded-full p-3 shadow-lg hover:bg-primary/90 transition-all"
      aria-label="Scroll to bottom"
    >
      <ArrowDown className="w-5 h-5" />
    </button>
  );
};
```

## Testing Checklist

### Manual Testing
- [ ] Send a user message → chat scrolls to bottom
- [ ] Receive agent response (streaming) → chat scrolls to bottom
- [ ] Scroll up manually → auto-scroll disabled
- [ ] Send new message while scrolled up → chat stays in position
- [ ] Scroll back to bottom → auto-scroll re-enabled
- [ ] Switch threads → chat loads at top, no auto-scroll
- [ ] Receive new message in current thread → scrolls to bottom

### Edge Cases
- [ ] Very long messages (multi-paragraph)
- [ ] Rapid message streaming
- [ ] Slow network (delayed streaming)
- [ ] Mobile viewport (smaller screens)
- [ ] Thread with 100+ messages

## Files to Modify/Create

### New Files
- `/frontend/hooks/useAutoScroll.ts` - Auto-scroll logic hook
- `/frontend/components/ScrollToBottomButton.tsx` - Optional UI enhancement

### Modified Files
- `/frontend/components/MessageHistory.tsx` - Integrate scroll hook
- `/frontend/components/ChatContainer.tsx` - Pass scroll controls
- `/frontend/hooks/useMessages.ts` - Coordinate with scroll state
- `/frontend/hooks/useChatThreads.ts` - Handle initial load flag

## Success Criteria

✅ **User Experience**
- Messages auto-scroll smoothly during active conversation
- Manual scroll position preserved when user browses history
- No jarring scrolls on thread load

✅ **Technical**
- Scroll state managed efficiently (no unnecessary re-renders)
- Works across all browsers (Chrome, Firefox, Safari, Edge)
- Responsive on mobile devices

✅ **Performance**
- No scroll lag during rapid message streaming
- Smooth scroll animation (CSS transition)

## Dependencies

- No new package dependencies required
- Uses native browser scroll APIs
- React refs and hooks

## Rollout Plan

1. **Phase 1**: Implement core auto-scroll hook
2. **Phase 2**: Integrate with MessageHistory and ChatContainer
3. **Phase 3**: Test with streaming messages
4. **Phase 4**: Add scroll-to-bottom button (optional)
5. **Phase 5**: QA and refinement

## Notes

- Consider using `IntersectionObserver` API for more efficient scroll detection
- May need to adjust scroll threshold (100px) based on UX feedback
- Smooth scroll may not work on older browsers (graceful degradation to instant scroll)

## References

- [MDN: Element.scrollTo()](https://developer.mozilla.org/en-US/docs/Web/API/Element/scrollTo)
- [React useRef Hook](https://react.dev/reference/react/useRef)
- [IntersectionObserver API](https://developer.mozilla.org/en-US/docs/Web/API/Intersection_Observer_API)
