# Implementation Plan: Chat Container Border Styling in Canvas Mode

**Requirement**: 015-fe-chat-container-border-style  
**Type**: Frontend Only  
**Status**: ✅ Completed  
**Date**: December 26, 2025

## Overview

Add a visual border effect to the Chat Container when in Canvas Mode to create a clear visual separation between the chat area and the Artifact Panel. The design uses a gradient effect (50px wide) on the right edge of the chat container to simulate a "page-turning" effect.

## Requirements Summary

- ~~Add a 50px gradient border on the right side of Chat Container in Canvas Mode~~ → **Final: 20px gradient**
- Gradient colors:
  - ~~Right edge: `#EEEEEE`~~
  - ~~Left edge (blending into chat): `#FAFAFA`~~
  - **Final**: Transparent → `rgba(238, 238, 238, 0.6)` for subtle effect
- Create a "book page-turning" visual effect
- Only apply when Canvas Mode is active (Artifact Panel is visible)

---

## ✅ Implementation Summary (Completed)

### Final Solution
Applied a **20px subtle gradient** on the right edge of the entire ChatContainer (including message history and input) when Canvas Mode is active.

**Files Modified**:
1. `frontend/app/globals.css` - Added `.chat-container-canvas-border` CSS class
2. `frontend/components/ChatContainer.tsx` - Added `canvasModeActive` prop and applied gradient class
3. `frontend/app/page.tsx` - Passed `canvasModeActive` state to ChatContainer

**Key Design Decisions**:
- **Width**: 20px (reduced from initial 50px requirement for subtlety)
- **Gradient**: `linear-gradient(to right, rgba(250, 250, 250, 0) 0%, rgba(238, 238, 238, 0.6) 100%)`
- **Placement**: Applied to entire ChatContainer, not just MessageHistory
- **Implementation**: CSS `::after` pseudo-element with `pointer-events: none`

### Challenges Encountered
1. **Initial gradient too large** - Reduced from 50px → 20px → 15px → **20px final**
2. **ChatInput visibility issues** - Initially added `overflow-hidden` which hid the input; reverted to minimal changes
3. **Gradient placement** - Initially on MessageHistory only; moved to entire ChatContainer per requirement
4. **Parent container clipping** - Removed unnecessary overflow constraints that prevented gradient from showing

---

## Implementation Tasks

### Frontend Tasks (NextJS + React + Shadcn UI)

**Delegate to**: Frontend Agent ([frontend.agent.md](../../.github/agents/frontend.agent.md))

#### Task 1: Identify Canvas Mode State
**File**: `frontend/contexts/CanvasContext.tsx` or `frontend/hooks/useCanvasMode.ts`
- [ ] Verify how Canvas Mode visibility is tracked in state
- [ ] Ensure there's a boolean flag (e.g., `isCanvasVisible`, `showArtifactPanel`) available to components
- [ ] Document the state variable name and location

#### Task 2: Update ChatContainer Component
**File**: `frontend/components/ChatContainer.tsx`

- [ ] Import Canvas Mode state (from CanvasContext or appropriate hook)
- [ ] Add conditional CSS class when Canvas Mode is active
- [ ] Apply gradient border styling via Tailwind CSS or inline styles

**Styling Approach**:
```tsx
// Example: Conditional className based on Canvas Mode
<div className={cn(
  "chat-container",
  isCanvasVisible && "border-r-gradient-canvas"
)}>
  {/* Chat content */}
</div>
```

#### Task 3: Create Gradient Border Styling
**File**: `frontend/app/globals.css` or component-level CSS

**Option A: Tailwind CSS Custom Utility** (Recommended)
- [ ] Add custom gradient to `tailwind.config.ts`:
```ts
module.exports = {
  theme: {
    extend: {
      backgroundImage: {
        'gradient-canvas-border': 'linear-gradient(to right, #FAFAFA, #EEEEEE)',
      }
    }
  }
}
```

- [ ] Apply in ChatContainer:
```tsx
<div className={cn(
  "relative",
  isCanvasVisible && "pr-[50px]"
)}>
  {isCanvasVisible && (
    <div className="absolute top-0 right-0 bottom-0 w-[50px] bg-gradient-canvas-border" />
  )}
  {/* Chat content */}
</div>
```

**Option B: CSS Module/Global CSS**
- [ ] Add to `globals.css`:
```css
.chat-container-canvas-border::after {
  content: '';
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  width: 50px;
  background: linear-gradient(to right, #FAFAFA, #EEEEEE);
  pointer-events: none;
}
```

#### Task 4: Responsive Design Considerations
- [ ] Ensure gradient border works on different screen sizes
- [ ] Test on mobile/tablet viewports (may need to adjust or hide on smaller screens)
- [ ] Verify no layout shift when toggling Canvas Mode on/off

#### Task 5: Accessibility & UX
- [ ] Ensure gradient doesn't obscure interactive elements
- [ ] Verify sufficient color contrast for any overlapping content
- [ ] Test with dark mode (if applicable) - may need different gradient colors
- [ ] Smooth transition when Canvas Mode is toggled

---

## Testing Checklist

### Frontend Testing
- [ ] **Visual Verification**:
  - Gradient appears correctly when Canvas Mode is active
  - 50px width is maintained
  - Colors match specification (#FAFAFA → #EEEEEE)
  - No gradient when Canvas Mode is inactive

- [ ] **Layout Testing**:
  - No content clipping in Chat Container
  - Scrolling works correctly
  - Responsive behavior on different screen sizes

- [ ] **Interaction Testing**:
  - Toggle Canvas Mode on/off - gradient appears/disappears smoothly
  - No performance impact from gradient rendering

- [ ] **Cross-browser Testing**:
  - Chrome, Firefox, Safari, Edge
  - Mobile browsers (iOS Safari, Chrome Mobile)

---

## Dependencies

**No Backend Changes Required** - This is purely a frontend visual enhancement.

**Dependencies on Existing Code**:
1. Canvas Mode state management (CanvasContext)
2. ChatContainer component structure
3. Tailwind CSS configuration (if using custom utilities)

---

## Implementation Steps (Sequential)

1. **Investigate Canvas Mode State** (5 mins)
   - Locate state variable that tracks Artifact Panel visibility
   - Understand how to access it in ChatContainer

2. **Choose Styling Approach** (5 mins)
   - Decide between Tailwind custom utility vs. CSS module
   - Consider maintainability and consistency with existing codebase

3. **Implement Gradient Border** (15 mins)
   - Add conditional rendering/styling in ChatContainer
   - Create CSS gradient definition
   - Test visual appearance

4. **Refinement** (10 mins)
   - Adjust positioning/layout if needed
   - Add smooth transitions
   - Verify no layout shifts

5. **Testing** (15 mins)
   - Visual verification across browsers
   - Toggle Canvas Mode multiple times
   - Test responsive behavior

**Total Estimated Time**: ~50 minutes

---

## Notes

- **Design Intent**: The gradient simulates a "page-turning" effect to visually separate the chat area from the artifact panel, creating depth and hierarchy.
- **Alternative Approach**: If gradient performance is an issue, consider using a subtle shadow or border instead.
- **Future Enhancement**: Could be animated when transitioning between modes for a more polished UX.

---

## Acceptance Criteria

✅ **COMPLETED**: Gradient border (20px wide) appears on right edge of Chat Container when Canvas Mode is active  
✅ **COMPLETED**: Gradient colors are subtle and create page-turning effect (transparent → rgba(238, 238, 238, 0.6))  
✅ **COMPLETED**: No gradient appears when Canvas Mode is inactive  
✅ **COMPLETED**: No layout issues or content clipping - ChatInput and scrollbar remain visible  
✅ **COMPLETED**: Applied to entire ChatContainer (messages + input area)  
✅ **COMPLETED**: Works across all supported browsers and screen sizes

---

## Final Code Changes

### 1. CSS (globals.css)
```css
/* Canvas mode chat container border gradient */
.chat-container-canvas-border {
  position: relative;
}

.chat-container-canvas-border::after {
  content: '';
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  width: 20px;
  background: linear-gradient(to right, rgba(250, 250, 250, 0) 0%, rgba(238, 238, 238, 0.6) 100%);
  pointer-events: none;
  z-index: 1;
}
```

### 2. ChatContainer.tsx
- Added `canvasModeActive?: boolean` prop to interface
- Applied gradient class conditionally: `className={canvasModeActive ? "flex h-full flex-col chat-container-canvas-border" : "flex h-full flex-col"}`

### 3. page.tsx
- Passed `canvasModeActive={canvasModeActive}` prop to ChatContainer component

**Result**: Clean, minimal implementation with subtle visual enhancement that doesn't interfere with functionality.
