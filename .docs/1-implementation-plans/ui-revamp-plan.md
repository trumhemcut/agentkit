# Implementation Plan: UI Revamp

**Requirement Reference**: `.docs/0-requirements/003-revamp-ui.md`  
**Created**: December 23, 2025  
**Owner**: Frontend Agent (see [frontend.agent.md](../../.github/agents/frontend.agent.md))

## Overview

Revamp the frontend layout to provide a ChatGPT-like user experience with:
- Collapsible sidebar with full-height layout
- Improved chat history navigation
- Cleaner, borderless design
- Persistent chatbox visibility

## Implementation Scope

This is a **Frontend-only** feature focusing on UI/UX improvements. No backend changes required.

---

## Tasks Breakdown

### 1. Frontend Tasks

**Owner**: Frontend Agent  
**Tech Stack**: NextJS, React, TypeScript, Shadcn UI, Tailwind CSS  
**Files to Modify**:
- `frontend/components/Sidebar.tsx`
- `frontend/components/Layout.tsx`
- `frontend/components/Header.tsx`
- `frontend/components/ChatContainer.tsx`
- `frontend/components/ChatHistory.tsx`
- `frontend/app/globals.css` (if needed for custom styling)

#### Task 1.1: Update Sidebar Component
**File**: `frontend/components/Sidebar.tsx`

**Requirements**:
- [ ] Make sidebar occupy 100% height
- [ ] Add header section with:
  - Logo on the left
  - Collapse/expand toggle icon on the right
- [ ] Implement collapse functionality:
  - Collapsed state: Show only icons
  - Expanded state: Show icons + text
  - Use state management (React useState/Context)
- [ ] Add "New Chat" button/menu item at the top
  - Icon on the left
  - Text label when expanded
- [ ] Add "Your chats" section header
- [ ] Style hover states with background color
- [ ] Remove all borders
- [ ] Add scrollbar for chat history overflow

**Implementation Notes**:
- Use Tailwind CSS classes: `h-screen`, `overflow-y-auto`, `transition-all`
- Consider using Shadcn UI `Button` component for "New Chat"
- Use Shadcn UI `ScrollArea` for chat history
- Store collapse state in React Context or localStorage for persistence
- Consider animation transitions for smooth collapse/expand

**TypeScript Interface**:
```typescript
interface SidebarProps {
  isCollapsed: boolean;
  onToggleCollapse: () => void;
  threads: ChatThread[];
  currentThreadId: string | null;
  onNewChat: () => void;
  onSelectThread: (threadId: string) => void;
  onDeleteThread: (threadId: string) => void;
}
```

#### Task 1.2: Update ChatHistory Component
**File**: `frontend/components/ChatHistory.tsx`

**Requirements**:
- [ ] Render historical chat threads as list items
- [ ] Each item displays:
  - Thread name/title (truncate if too long)
  - Three-dot menu button on the right (visible on hover)
- [ ] No icon on the left of thread items
- [ ] Three-dot menu shows "Delete" option
- [ ] Implement hover background color
- [ ] Handle thread selection (navigate to thread)
- [ ] Handle thread deletion (with confirmation if needed)
- [ ] Support scrolling for many items

**Implementation Notes**:
- Use Shadcn UI `DropdownMenu` for three-dot menu
- Use Shadcn UI `ScrollArea` for list scrolling
- Add hover effects with Tailwind: `hover:bg-secondary`
- Consider using `react-icons` or Lucide icons for three-dot menu
- Implement optimistic UI updates for deletions

**TypeScript Interface**:
```typescript
interface ChatHistoryProps {
  threads: ChatThread[];
  currentThreadId: string | null;
  isCollapsed: boolean;
  onSelectThread: (threadId: string) => void;
  onDeleteThread: (threadId: string) => void;
}

interface ChatHistoryItemProps {
  thread: ChatThread;
  isActive: boolean;
  isCollapsed: boolean;
  onSelect: () => void;
  onDelete: () => void;
}
```

#### Task 1.3: Update Layout Component
**File**: `frontend/components/Layout.tsx`

**Requirements**:
- [ ] Ensure sidebar is full height (100vh)
- [ ] Remove borders between sidebar and main content
- [ ] Adjust main content area to accommodate new sidebar width
- [ ] Handle collapsed sidebar state (reduce width)
- [ ] Ensure responsive layout

**Implementation Notes**:
- Use CSS Grid or Flexbox for layout
- Sidebar width: ~260px expanded, ~60px collapsed
- Use Tailwind: `grid grid-cols-[260px_1fr]` or `grid-cols-[60px_1fr]`
- Add transition for smooth width changes
- Remove all border utilities: no `border-r`, `border-l`

#### Task 1.4: Update Header Component
**File**: `frontend/components/Header.tsx`

**Requirements**:
- [ ] Remove borders from header
- [ ] Ensure header spans full width of main content area
- [ ] Maintain clean, minimal design

**Implementation Notes**:
- Remove Tailwind classes: `border-b`
- Consider subtle shadow instead of border if visual separation needed
- Ensure proper spacing and padding

#### Task 1.5: Update ChatContainer Component
**File**: `frontend/components/ChatContainer.tsx`

**Requirements**:
- [ ] Always show the chatbox/input area
- [ ] Ensure chatbox is visible even when no messages
- [ ] Remove any conditional rendering that hides chatbox

**Implementation Notes**:
- Remove conditions like: `{messages.length > 0 && <ChatInput />}`
- Always render `<ChatInput />` component
- Consider showing placeholder or welcome message when no chat is active
- Ensure proper spacing and layout

#### Task 1.6: Add Global Styles
**File**: `frontend/app/globals.css` (if needed)

**Requirements**:
- [ ] Define custom CSS variables for sidebar widths
- [ ] Add smooth transition animations
- [ ] Define hover colors if not using Tailwind defaults

**Implementation Notes**:
```css
:root {
  --sidebar-width-expanded: 260px;
  --sidebar-width-collapsed: 60px;
  --transition-duration: 300ms;
}

.sidebar-transition {
  transition: width var(--transition-duration) ease-in-out;
}
```

---

## State Management

### Required State
```typescript
// Global or Context state
interface UIState {
  isSidebarCollapsed: boolean;
  currentThreadId: string | null;
  threads: ChatThread[];
}

// Actions
- toggleSidebar(): void
- setCurrentThread(id: string): void
- deleteThread(id: string): void
- createNewThread(): void
```

### Recommendations
- Use React Context for sidebar collapse state (shared across components)
- Store collapse preference in localStorage for persistence
- Use existing `useChatThreads` hook for thread management
- Consider adding `useLocalStorage` hook for sidebar state

---

## API Integration

**No backend changes required** - This is purely a frontend UI update.

However, ensure these existing APIs are properly integrated:
- GET /threads - Fetch chat history
- DELETE /threads/:id - Delete thread
- POST /threads - Create new thread

---

## Dependencies

### Component Dependencies
1. Update `Sidebar` → depends on `ChatHistory`
2. Update `ChatHistory` → can be done independently
3. Update `Layout` → depends on `Sidebar` width states
4. Update `Header` → can be done independently
5. Update `ChatContainer` → can be done independently

### Execution Order
1. ✅ **Phase 1**: Update `ChatHistory` component (independent)
2. ✅ **Phase 2**: Update `Sidebar` component (uses ChatHistory)
3. ✅ **Phase 3**: Update `Layout` component (uses Sidebar)
4. ✅ **Phase 4**: Update `Header` component (independent)
5. ✅ **Phase 5**: Update `ChatContainer` component (independent)
6. ✅ **Phase 6**: Add global styles if needed
7. ✅ **Phase 7**: Test and refine

---

## Testing Checklist

### Functional Testing
- [ ] Sidebar collapses/expands smoothly
- [ ] "New Chat" button creates new thread
- [ ] Chat history items are clickable and navigate correctly
- [ ] Three-dot menu appears on hover
- [ ] Delete option removes thread from list
- [ ] Scrollbar appears when many threads exist
- [ ] Chatbox is always visible
- [ ] Sidebar state persists across page refreshes

### Visual Testing
- [ ] No borders on sidebar, header, or content
- [ ] Hover effects work on menu items
- [ ] Collapsed sidebar shows only icons
- [ ] Expanded sidebar shows icons + text
- [ ] Logo and collapse icon are properly positioned
- [ ] Smooth transitions for collapse/expand
- [ ] Responsive layout works on different screen sizes

### Edge Cases
- [ ] Empty chat history state
- [ ] Very long thread names (truncation)
- [ ] Many threads (scrolling performance)
- [ ] Rapid collapse/expand toggling
- [ ] Deleting currently active thread

---

## UI/UX Considerations

### Design Specs
- **Sidebar Width**: 260px (expanded), 60px (collapsed)
- **Transition Duration**: 300ms ease-in-out
- **Hover Background**: Use Shadcn UI secondary color
- **Icons**: Use Lucide icons (consistent with Shadcn UI)
- **Scrollbar**: Custom styled or use Shadcn UI ScrollArea

### Accessibility
- [ ] Keyboard navigation support (Tab, Enter, Escape)
- [ ] ARIA labels for icon-only buttons in collapsed state
- [ ] Focus indicators for interactive elements
- [ ] Screen reader announcements for state changes

---

## Implementation Notes

### Existing Patterns to Follow
Reference [frontend.agent.md](../../.github/agents/frontend.agent.md) for:
- Shadcn UI component usage patterns
- TypeScript interface conventions
- React hooks patterns
- Tailwind CSS utility classes

### New Components to Create (Optional)
Consider extracting these for better organization:
- `SidebarHeader.tsx` - Logo and collapse toggle
- `SidebarNavItem.tsx` - Individual menu item component
- `ChatThreadItem.tsx` - Individual thread list item

---

## Definition of Done

- [ ] All tasks completed and tested
- [ ] Code follows TypeScript best practices
- [ ] Shadcn UI components properly integrated
- [ ] Responsive design works on mobile/tablet/desktop
- [ ] No console errors or warnings
- [ ] Smooth animations and transitions
- [ ] Accessibility requirements met
- [ ] Code reviewed and approved

---

## Hand-off to Frontend Agent

Frontend Agent: Please implement the tasks outlined in this plan following the patterns in [frontend.agent.md](../../.github/agents/frontend.agent.md). Focus on:
1. Component structure and TypeScript interfaces
2. Shadcn UI integration
3. Tailwind CSS styling
4. State management with React hooks
5. Smooth user experience with transitions

No backend changes are required for this feature.
