# Implementation Plan: Auto-scroll Chat Messages

## Requirement Summary
**Issue**: When agent sends messages during chat, the scrollbar does not automatically scroll to the bottom to show the latest message.

**Goal**: Implement automatic scrolling to the bottom of the chat when new messages arrive (both user and agent messages).

---

## 1. Backend (LangGraph + AG-UI)

**No backend changes required** - This is purely a frontend UI behavior enhancement.

---

## 2. Protocol (AG-UI)

**No protocol changes required** - Existing AG-UI events (`TEXT_MESSAGE_CHUNK`, `RUN_FINISHED`, etc.) already provide the necessary message data.

**Note**: Frontend will use existing message events to trigger scroll behavior.

---

## 3. Frontend (AG-UI + React)

**Delegate to Frontend Agent** - See [.github/agents/frontend.agent.md](.github/agents/frontend.agent.md)

### 3.1 Analysis Phase
- [ ] Identify all chat message container components:
  - `components/ChatContainer.tsx`
  - `components/MessageHistory.tsx`
  - `components/ChatHistory.tsx`
- [ ] Review scroll container structure and ref usage
- [ ] Check existing scroll behavior in Canvas mode vs Chat mode

### 3.2 Implementation Tasks

#### Task 3.2.1: Add Auto-scroll Hook
**File**: `frontend/hooks/useAutoScroll.ts` (new)

Create a reusable hook for auto-scroll behavior:
```typescript
// Features:
// - useRef for scroll container
// - Auto-scroll when messages change
// - Smooth scroll behavior
// - Optional scroll threshold (e.g., only scroll if near bottom)
// - Manual scroll detection (pause auto-scroll if user scrolls up)
```

**Requirements**:
- Detect when user manually scrolls up (disable auto-scroll)
- Re-enable auto-scroll when user scrolls near bottom
- Handle smooth scrolling animation
- TypeScript type safety

#### Task 3.2.2: Integrate Auto-scroll in MessageHistory
**File**: `frontend/components/MessageHistory.tsx`

- [ ] Import `useAutoScroll` hook
- [ ] Apply scroll ref to message container
- [ ] Trigger scroll on `messages` array changes
- [ ] Handle both user messages and agent responses

#### Task 3.2.3: Integrate Auto-scroll in ChatContainer
**File**: `frontend/components/ChatContainer.tsx`

- [ ] Ensure scroll container has proper ref
- [ ] Coordinate scroll behavior with message streaming
- [ ] Test with AG-UI real-time events (TEXT_MESSAGE_CHUNK)

#### Task 3.2.4: Handle Canvas Mode
**File**: `frontend/components/Canvas/*` (if applicable)

- [ ] Check if Canvas mode has separate chat scroll
- [ ] Apply same auto-scroll logic if needed
- [ ] Ensure consistency across modes

### 3.3 Testing Requirements

- [ ] **User sends message**: Chat scrolls to bottom immediately
- [ ] **Agent responds**: Chat scrolls as message chunks arrive (streaming)
- [ ] **User scrolls up**: Auto-scroll pauses (user is reading history)
- [ ] **User scrolls to bottom**: Auto-scroll re-enables
- [ ] **Long messages**: Scroll behavior works with messages exceeding viewport
- [ ] **Multiple messages**: Sequential messages trigger smooth scrolling
- [ ] **Mode switching**: Scroll behavior consistent in Chat vs Canvas mode

### 3.4 Edge Cases

- [ ] Handle rapid message arrivals (throttle scroll calls)
- [ ] Prevent scroll jank during text streaming
- [ ] Handle window resize (recalculate scroll position)
- [ ] Accessibility: Respect user's `prefers-reduced-motion`

---

## 4. Dependencies & Order

### Execution Order:
1. **Create `useAutoScroll` hook** (independent, foundational)
2. **Integrate in MessageHistory** (depends on hook)
3. **Integrate in ChatContainer** (depends on hook)
4. **Test and refine** (depends on integration)

### External Dependencies:
- None (uses existing React refs and useEffect)

---

## 5. Success Criteria

✅ Chat automatically scrolls to bottom when:
- User sends a new message
- Agent starts responding
- Agent message is streaming (real-time chunks)

✅ Auto-scroll pauses when:
- User manually scrolls up to read history

✅ Auto-scroll resumes when:
- User scrolls back near the bottom (threshold: ~100px)

✅ Behavior is smooth and performant:
- No scroll jank or flashing
- Respects reduced motion preferences

---

## 6. Implementation Notes

### Recommended Approach:
Use **scroll threshold** pattern:
```typescript
// Pseudo-code
const isNearBottom = scrollHeight - scrollTop - clientHeight < 100;
if (isNearBottom || isNewMessage) {
  scrollToBottom({ behavior: 'smooth' });
}
```

### Accessibility:
```typescript
// Respect user preferences
const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
const scrollBehavior = prefersReducedMotion ? 'auto' : 'smooth';
```

### Performance:
- Use `useCallback` for scroll handlers
- Debounce scroll position checks (e.g., 100ms)
- Avoid unnecessary re-renders

---

## 7. Reference Files

**Frontend Components**:
- [frontend/components/MessageHistory.tsx](../../frontend/components/MessageHistory.tsx)
- [frontend/components/ChatContainer.tsx](../../frontend/components/ChatContainer.tsx)
- [frontend/components/ChatHistory.tsx](../../frontend/components/ChatHistory.tsx)

**Hooks**:
- [frontend/hooks/useMessages.ts](../../frontend/hooks/useMessages.ts) - Reference for message state
- [frontend/hooks/useAGUI.ts](../../frontend/hooks/useAGUI.ts) - Reference for AG-UI integration

**Knowledge Base**:
- [.docs/2-knowledge-base/](../2-knowledge-base/) - Check for existing scroll patterns

---

## 8. Handoff to Frontend Agent

**Frontend Agent** - See [.github/agents/frontend.agent.md](.github/agents/frontend.agent.md):
1. Create `useAutoScroll` hook with scroll threshold logic
2. Integrate hook into `MessageHistory` and `ChatContainer` components
3. Test with both user messages and AG-UI streaming responses
4. Ensure accessibility (reduced motion) and performance (debounce)
5. Update knowledge base with autoscroll pattern documentation

**No Backend Agent involvement required for this feature.**
