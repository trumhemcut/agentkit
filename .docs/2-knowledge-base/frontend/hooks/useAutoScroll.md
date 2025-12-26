# useAutoScroll Hook

**File**: `/frontend/hooks/useAutoScroll.ts`

## Overview

Custom React hook that manages intelligent auto-scroll behavior for chat messages. Automatically scrolls to bottom when new messages arrive, but preserves user's scroll position when they've manually scrolled up to read history.

## Features

- ✅ **Smart Auto-Scroll**: Scrolls to bottom only when user is near bottom
- ✅ **User Intent Preservation**: Maintains scroll position when user scrolls up
- ✅ **Initial Load Handling**: Skips auto-scroll on thread history load
- ✅ **Smooth Scrolling**: Uses CSS smooth scroll for better UX
- ✅ **Scroll Threshold**: Configurable distance from bottom (default: 100px)

## API

### Hook Signature

```typescript
function useAutoScroll(
  dependencies: any[],
  options?: UseAutoScrollOptions
): UseAutoScrollReturn
```

### Options

```typescript
interface UseAutoScrollOptions {
  /**
   * Whether this is the initial load (no auto-scroll on initial load)
   */
  isInitialLoad?: boolean;
  
  /**
   * Distance from bottom (in pixels) to consider "at bottom"
   * Default: 100
   */
  scrollThreshold?: number;
}
```

### Return Value

```typescript
interface UseAutoScrollReturn {
  /**
   * Ref to attach to scrollable container
   */
  scrollRef: RefObject<HTMLDivElement>;
  
  /**
   * Scroll event handler to attach to container
   */
  handleScroll: () => void;
  
  /**
   * Function to manually scroll to bottom
   */
  scrollToBottom: (smooth?: boolean) => void;
  
  /**
   * Whether auto-scroll is currently enabled
   */
  shouldAutoScroll: boolean;
  
  /**
   * Function to check if scroll is near bottom
   */
  isNearBottom: () => boolean;
}
```

## Usage

### Basic Example

```typescript
import { useAutoScroll } from '@/hooks/useAutoScroll';

function ChatComponent({ messages }) {
  const { scrollRef, handleScroll, scrollToBottom } = useAutoScroll([messages]);

  return (
    <div 
      ref={scrollRef}
      onScroll={handleScroll}
      className="overflow-y-auto"
    >
      {messages.map(msg => (
        <MessageBubble key={msg.id} message={msg} />
      ))}
    </div>
  );
}
```

### With Initial Load Flag

```typescript
function ChatComponent({ threadId, messages }) {
  const [isInitialLoad, setIsInitialLoad] = useState(true);

  useEffect(() => {
    setIsInitialLoad(true);
    // Load messages...
    setTimeout(() => setIsInitialLoad(false), 100);
  }, [threadId]);

  const { scrollRef, handleScroll } = useAutoScroll(
    [messages],
    { isInitialLoad }
  );

  return (
    <div ref={scrollRef} onScroll={handleScroll}>
      {/* Messages */}
    </div>
  );
}
```

## Implementation Details

### Scroll State Tracking

The hook tracks:
- **shouldAutoScroll**: Boolean flag indicating if auto-scroll is enabled
- **isUserScrolling**: Temporary flag set during user scroll events
- **previousScrollHeight**: Previous scroll height to detect new content

### Auto-Scroll Logic

1. **User scrolls manually** → `handleScroll()` fired
   - Check if position is near bottom (< 100px from bottom)
   - Update `shouldAutoScroll` based on position
   - Set `isUserScrolling` flag for 150ms

2. **Dependencies change** (new message arrives) → `useEffect` triggered
   - Skip if `isInitialLoad` is true
   - Skip if no new content (scroll height unchanged)
   - Skip if user is actively scrolling
   - Auto-scroll only if `shouldAutoScroll` is true

3. **User sends message** → Force scroll to bottom
   - Call `scrollToBottom(true)` in `ChatContainer.sendMessage`
   - Uses `setTimeout(() => scrollToBottom(true), 0)` to ensure DOM is updated
   - Always scrolls regardless of `shouldAutoScroll` state
   - Re-enables auto-scroll after force scroll

4. **Manual scroll to bottom** → `scrollToBottom()` called
   - Scroll to bottom with smooth animation
   - Re-enable auto-scroll

5. **Layout changes** (e.g., canvas mode toggle) → `useLayoutEffect` triggered
   - Re-check if scroll position is near bottom
   - Update `shouldAutoScroll` flag if position changed
   - Ensures auto-scroll works correctly after container resize

### Canvas Mode Compatibility

The hook includes special handling for canvas mode:
- When canvas mode activates, the chat container resizes from full width to 1/3 width
- A `useLayoutEffect` re-evaluates the scroll position after layout changes
- This ensures auto-scroll continues working even when the container dimensions change
- The layout effect runs synchronously after DOM mutations but before paint

### Scroll Threshold

The "near bottom" threshold is configurable:
- **Default**: 100px from bottom
- **Purpose**: Gives users buffer zone - don't need to be exactly at bottom
- **UX**: Feels natural - small scrolls up don't disable auto-scroll

## Integration with useMessages

The `useMessages` hook integrates `useAutoScroll` and exports `scrollToBottom` for manual control:

```typescript
export function useMessages(threadId: string | null, options?: UseMessagesOptions) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isInitialLoad, setIsInitialLoad] = useState(true);

  // Use auto-scroll with messages dependency
  const { scrollRef, handleScroll, scrollToBottom } = useAutoScroll(
    [messages],
    { isInitialLoad }
  );

  // Load messages when thread changes
  useEffect(() => {
    if (!threadId) {
      setMessages([]);
      setIsInitialLoad(true);
      return;
    }

    setIsInitialLoad(true);
    const thread = StorageService.getThread(threadId);
    setMessages(thread?.messages || []);
    
    // Mark initial load complete after render
    setTimeout(() => setIsInitialLoad(false), 100);
  }, [threadId]);

  return {
    messages,
    scrollRef,
    handleScroll,
    scrollToBottom, // Export for manual control
    // ... other methods
  };
}
```

### Force Scroll on User Message Send

In `ChatContainer`, we force scroll to bottom when user sends a new message, regardless of current scroll position:

```typescript
const { scrollToBottom } = useMessages(threadId);

const sendMessage = async (content: string) => {
  // Add user message
  addMessage(userMessage);
  
  // Force scroll to bottom when user sends message
  setTimeout(() => scrollToBottom(true), 0);
  
  // Continue with agent response...
};
```

**Why setTimeout with delay 0?**
- Ensures the message is added to DOM before scrolling
- Allows React to complete the render cycle
- Smooth scroll animation works correctly

## Performance Considerations

### Debouncing

User scroll events are debounced with 150ms timeout:
```typescript
scrollTimeoutRef.current = setTimeout(() => {
  setIsUserScrolling(false);
}, 150);
```

This prevents auto-scroll from triggering during rapid user scrolling.

### requestAnimationFrame

Auto-scroll uses `requestAnimationFrame` for smoother animation:
```typescript
requestAnimationFrame(() => {
  scrollToBottom(true);
});
```

### Content Change Detection

Only auto-scrolls when scroll height actually changes:
```typescript
const hasNewContent = currentScrollHeight !== previousScrollHeight.current;
if (!hasNewContent) return;
```

## Browser Compatibility

- **Smooth Scrolling**: Uses `scrollTo({ behavior: 'smooth' })`
  - Supported in all modern browsers
  - Gracefully degrades to instant scroll in older browsers
  
- **Element.scrollHeight**: Standard API, universally supported

## Testing Checklist

### Manual Testing Scenarios

- [x] Send user message → chat scrolls to bottom (**force scroll**)
- [x] Receive agent response (streaming) → chat scrolls during stream
- [x] Scroll up manually → auto-scroll disabled
- [x] Send new message while scrolled up → **chat force scrolls to bottom**
- [x] Scroll back to bottom → auto-scroll re-enabled
- [x] Switch threads → chat loads at top, no auto-scroll
- [x] Receive new message in current thread → scrolls to bottom

### Edge Cases

- [ ] Very long messages (multi-paragraph)
- [ ] Rapid message streaming
- [ ] Slow network (delayed streaming)
- [ ] Mobile viewport (touch scrolling)
- [ ] Thread with 100+ messages
- [ ] Empty thread (no messages)

## Future Enhancements

### Scroll-to-Bottom Button

Add a floating button when user scrolls up:

```typescript
export function ScrollToBottomButton({ 
  visible, 
  onClick 
}: { 
  visible: boolean; 
  onClick: () => void 
}) {
  if (!visible) return null;

  return (
    <button
      onClick={onClick}
      className="fixed bottom-20 right-8 bg-primary rounded-full p-3 shadow-lg"
    >
      <ArrowDown className="w-5 h-5" />
    </button>
  );
}
```

Usage:
```typescript
const { scrollToBottom, shouldAutoScroll } = useAutoScroll([messages]);

return (
  <>
    <MessageHistory />
    <ScrollToBottomButton 
      visible={!shouldAutoScroll}
      onClick={() => scrollToBottom()}
    />
  </>
);
```

### IntersectionObserver

For better performance with large message lists, consider using `IntersectionObserver`:

```typescript
const lastMessageRef = useRef<HTMLDivElement>(null);

useEffect(() => {
  if (!lastMessageRef.current) return;
  
  const observer = new IntersectionObserver(
    ([entry]) => {
      setShouldAutoScroll(entry.isIntersecting);
    },
    { threshold: 0.1 }
  );
  
  observer.observe(lastMessageRef.current);
  return () => observer.disconnect();
}, [messages.length]);
```

## Related Files

- [useMessages.md](./useMessages.md) - Message state management
- [MessageHistory.tsx](../components/MessageHistory.md) - Message list component
- [ChatContainer.tsx](../components/ChatContainer.md) - Main chat interface

## References

- [MDN: Element.scrollTo()](https://developer.mozilla.org/en-US/docs/Web/API/Element/scrollTo)
- [MDN: IntersectionObserver](https://developer.mozilla.org/en-US/docs/Web/API/Intersection_Observer_API)
- [React useRef Hook](https://react.dev/reference/react/useRef)
