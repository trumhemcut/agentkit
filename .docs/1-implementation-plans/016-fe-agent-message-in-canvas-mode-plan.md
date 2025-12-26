# Implementation Plan: Optimize Message Display in Canvas Mode

## Requirement Summary
In canvas mode, the chat container has limited display space. This plan optimizes the message display by:
- **Agent Messages**: Remove avatar icon, display full content within the message bubble
- **User Messages**: Remove avatar icon, keep content format unchanged

## Current State Analysis
- `ChatContainer` receives `canvasModeActive` prop to track canvas mode state
- `MessageHistory` renders message list using `MessageBubble` component
- `MessageBubble` routes to `AgentMessageBubble` or `UserMessageBubble` based on role
- Both message bubbles currently display `AvatarIcon` component
- AgentMessageBubble uses markdown rendering with ReactMarkdown

## Implementation Layers

### 1. Frontend (AG-UI) - TypeScript/React/Shadcn UI

**Delegate to Frontend Agent** - See [frontend.agent.md](../../../.github/agents/frontend.agent.md)

#### Task 1: Pass Canvas Mode State Through Component Tree ✓ COMPLETED
**File**: [frontend/components/MessageHistory.tsx](../../../frontend/components/MessageHistory.tsx)
- ✓ Added `canvasModeActive?: boolean` prop to `MessageHistoryProps` interface
- ✓ Passed `canvasModeActive` to each `MessageBubble` component

**File**: [frontend/components/MessageBubble.tsx](../../../frontend/components/MessageBubble.tsx)
- ✓ Added `canvasModeActive?: boolean` prop to `MessageBubbleProps` interface
- ✓ Passed `canvasModeActive` to both `UserMessageBubble` and `AgentMessageBubble`

**File**: [frontend/components/ChatContainer.tsx](../../../frontend/components/ChatContainer.tsx)
- ✓ Passed `canvasModeActive` prop to `MessageHistory` component

#### Task 2: Update AgentMessageBubble for Canvas Mode ✓ COMPLETED
**File**: [frontend/components/AgentMessageBubble.tsx](../../../frontend/components/AgentMessageBubble.tsx)
- ✓ Added `canvasModeActive?: boolean` prop to `AgentMessageBubbleProps` interface
- ✓ Conditionally rendered `AvatarIcon` only when NOT in canvas mode
- ✓ Adjusted layout spacing with conditional gap: `gap-0` in canvas mode, `gap-3` in regular mode
- ✓ Removed agent name/title display for cleaner UI
- ✓ Changed from `max-w-[70%]` to `flex-1` to make card fill full width
- ✓ Maintained markdown rendering and all message features

**Implementation**:
```tsx
<div className={cn("flex p-4 justify-start", canvasModeActive ? "gap-0" : "gap-3")}>
  {!canvasModeActive && <AvatarIcon role="agent" />}
  <div className="flex flex-col gap-1 flex-1">
    <Card className="bg-muted border-0">
      {/* content */}
    </Card>
  </div>
</div>
```

#### Task 3: Update UserMessageBubble for Canvas Mode ✓ COMPLETED
**File**: [frontend/components/UserMessageBubble.tsx](../../../frontend/components/UserMessageBubble.tsx)
- ✓ Added `canvasModeActive?: boolean` prop to `UserMessageBubbleProps` interface
- ✓ Conditionally rendered `AvatarIcon` only when NOT in canvas mode
- ✓ Adjusted layout spacing with conditional gap: `gap-0` in canvas mode, `gap-3` in regular mode
- ✓ Kept content format unchanged
- ✓ Maintained timestamp display

**Implementation**:
```tsx
<div className={`flex p-4 justify-end ${canvasModeActive ? 'gap-0' : 'gap-3'}`}>
  <div className="flex flex-col gap-1 max-w-[70%] items-end">
    {/* content */}
  </div>
  {!canvasModeActive && <AvatarIcon role="user" />}
</div>
```

### 2. Testing & Validation

#### Manual Testing Checklist
- [ ] Toggle canvas mode on/off and verify avatars appear/disappear correctly
- [ ] Verify agent messages display full markdown content without avatar
- [ ] Verify user messages display full text content without avatar
- [ ] Check spacing and alignment in both regular and canvas modes
- [ ] Test with long messages to ensure content isn't cut off
- [ ] Verify timestamp display remains correct
- [ ] Test markdown rendering in agent messages (code blocks, links, etc.)
- [ ] Check responsive behavior in narrow canvas widths

#### Visual Regression Testing
- Compare message layout in regular mode vs canvas mode
- Verify no layout breaks when toggling between modes
- Check that message width utilization improves in canvas mode

## Implementation Order

1. ✓ **Pass Canvas Mode State** (Task 1)
   - ✓ Update MessageHistory interface and pass prop
   - ✓ Update MessageBubble interface and pass prop
   - ✓ Connect ChatContainer to MessageHistory

2. ✓ **Update AgentMessageBubble** (Task 2)
   - ✓ Add prop and conditional rendering for avatar
   - ✓ Adjust layout spacing (conditional gap)
   - ✓ Remove agent name/title display
   - ✓ Make card full width with `flex-1`

3. ✓ **Update UserMessageBubble** (Task 3)
   - ✓ Add prop and conditional rendering for avatar
   - ✓ Adjust layout spacing (conditional gap)

4. **Integration Testing** - PENDING USER VALIDATION
   - Test complete flow in canvas mode
   - Verify no regressions in regular mode

## Dependencies

- No new packages required
- No backend changes needed
- No protocol changes needed

## Technical Considerations

### CSS/Styling
- Use conditional className or inline styles to adjust spacing
- Consider using Tailwind's conditional classes: `${canvasModeActive ? 'gap-0' : 'gap-3'}`
- Ensure Shadcn UI Card component maintains proper padding

### State Management
- Canvas mode state already exists in ChatContainer via `canvasModeActive` prop
- Simply pass this state down the component tree
- No additional state management needed

### Accessibility
- Even without avatars, maintain proper semantic HTML structure
- Ensure messages are still clearly distinguishable (agent vs user)
- Keep ARIA labels if present

## Success Criteria

- [x] Agent messages in canvas mode display without avatar icon
- [x] User messages in canvas mode display without avatar icon
- [x] Full message content is visible in both cases (agent card now uses `flex-1` for full width)
- [x] Layout spacing is optimized for narrow canvas width (conditional gap: 0 vs 3)
- [x] Agent name/title removed for cleaner display
- [ ] No regressions in regular (non-canvas) mode - PENDING USER TESTING
- [ ] Smooth visual transition when toggling canvas mode - PENDING USER TESTING
- [x] All message features (markdown, timestamps, etc.) work correctly (no code changes to these features)

## Notes

This is a pure frontend optimization task. No backend or protocol changes are needed. The implementation focuses on conditional rendering based on the existing `canvasModeActive` state.

The key is to maximize the chat container space in canvas mode while maintaining all message functionality and visual clarity.

---

## Implementation Summary

**Status**: ✓ COMPLETED (Pending User Testing)

**Date Completed**: December 26, 2025

**Changes Made**:
1. Added `canvasModeActive` prop through component hierarchy (ChatContainer → MessageHistory → MessageBubble → Agent/UserMessageBubble)
2. Conditionally hide avatar icons in canvas mode using `{!canvasModeActive && <AvatarIcon />}`
3. Applied conditional spacing: `gap-0` in canvas mode, `gap-3` in regular mode
4. Removed agent name/title display from AgentMessageBubble for cleaner UI
5. Changed agent message card from `max-w-[70%]` to `flex-1` for full-width display

**Files Modified**:
- [frontend/components/ChatContainer.tsx](../../../frontend/components/ChatContainer.tsx)
- [frontend/components/MessageHistory.tsx](../../../frontend/components/MessageHistory.tsx)
- [frontend/components/MessageBubble.tsx](../../../frontend/components/MessageBubble.tsx)
- [frontend/components/AgentMessageBubble.tsx](../../../frontend/components/AgentMessageBubble.tsx)
- [frontend/components/UserMessageBubble.tsx](../../../frontend/components/UserMessageBubble.tsx)

**Testing Required**: Manual testing to verify no visual regressions in regular mode and proper display in canvas mode.
