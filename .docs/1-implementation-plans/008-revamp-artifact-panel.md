# Implementation Plan: Revamp Artifact Panel

**Requirement**: `008-Revamp-the-artifact-pannel.md`  
**Created**: 2025-12-25  
**Status**: Ready for Implementation

## Overview

Revamp the artifact panel to enhance interaction with chat by customizing the BlockNoteView experience. The main goals are:
- Disable the default BlockNote context menu
- Add a custom horizontal context menu with "Chat with agent" action
- Highlight selected text in yellow when "Chat with agent" is clicked
- Auto-focus the chat input for seamless interaction

## Architecture Summary

### Component Stack
```
TextRenderer.tsx
  ├─ BlockNoteView (from @blocknote/shadcn)
  │   ├─ Custom context menu (horizontal)
  │   └─ Text selection handling
  └─ Text highlighting system
```

### Data Flow
```
User selects text → Custom menu appears → User clicks "Chat with agent" 
→ Text highlighted (yellow) → Chat input focused → User can type message about selected text
```

---

## Implementation Tasks

### 1. Backend Tasks
**Delegate to**: Backend Agent ([backend.agent.md](.github/agents/backend.agent.md))

#### Task 1.1: No backend changes required ✅
- This feature is purely frontend-based
- Backend canvas agent endpoints remain unchanged
- No new API endpoints needed

---

### 2. Protocol (AG-UI)
**Communication Contract**

#### Task 2.1: Define new context menu event (optional enhancement)
- **Optional**: Consider adding AG-UI event for text selection
- Format: `TEXT_SELECTED` event with selected text range
- This would allow backend to track user interactions for future features
- **Note**: Not required for MVP - can be added later

---

### 3. Frontend Tasks
**Delegate to**: Frontend Agent ([frontend.agent.md](.github/agents/frontend.agent.md))

#### Task 3.1: Disable Default BlockNote Context Menu
**File**: `frontend/components/Canvas/TextRenderer.tsx`

**Actions**:
1. Configure BlockNoteView to disable default context menu
2. Use BlockNote's `formattingToolbar` prop or CSS override
3. Research BlockNote API for context menu configuration
4. Test that default right-click menu is fully suppressed

**Technical Details**:
```tsx
// Option 1: Via BlockNoteView props
<BlockNoteView
  editor={editor}
  onChange={handleChange}
  editable={!isStreaming}
  theme="light"
  formattingToolbar={false} // Disable toolbar
  // Additional props to explore
/>

// Option 2: Via CSS override
.bn-container .bn-formatting-toolbar {
  display: none !important;
}
```

**Dependencies**: Research BlockNote documentation for proper API usage

---

#### Task 3.2: Implement Text Selection Detection
**File**: `frontend/components/Canvas/TextRenderer.tsx`

**Actions**:
1. Add `onSelectionChange` handler to detect when user selects text
2. Track selected text range and content
3. Store selection state in component state
4. Handle selection clearing

**Implementation Pattern**:
```tsx
const [selectedText, setSelectedText] = useState<{
  text: string;
  range: { start: number; end: number };
} | null>(null);

useEffect(() => {
  // Listen to editor selection changes
  const handleSelection = () => {
    const selection = editor.getSelection();
    if (selection && selection.toString().trim()) {
      setSelectedText({
        text: selection.toString(),
        range: { start: selection.start, end: selection.end }
      });
    } else {
      setSelectedText(null);
    }
  };
  
  editor.onSelectionChange(handleSelection);
  return () => editor.offSelectionChange(handleSelection);
}, [editor]);
```

**Dependencies**: BlockNote editor selection API

---

#### Task 3.3: Create Custom Horizontal Context Menu Component
**File**: `frontend/components/Canvas/ArtifactContextMenu.tsx` (new file)

**Actions**:
1. Create a new component for the custom context menu
2. Design horizontal menu layout with "Chat with agent" button
3. Position menu near selected text (above or below)
4. Add smooth animation for menu appearance/disappearance
5. Use Shadcn UI components for consistency

**Component Structure**:
```tsx
interface ArtifactContextMenuProps {
  selectedText: string;
  position: { x: number; y: number };
  onChatWithAgent: (text: string) => void;
  onClose: () => void;
}

export function ArtifactContextMenu({
  selectedText,
  position,
  onChatWithAgent,
  onClose
}: ArtifactContextMenuProps) {
  return (
    <div 
      className="absolute z-50 bg-white border rounded-lg shadow-lg p-2 flex items-center gap-2"
      style={{ top: position.y, left: position.x }}
    >
      <Button
        variant="ghost"
        size="sm"
        onClick={() => onChatWithAgent(selectedText)}
        className="flex items-center gap-2"
      >
        <MessageCircle className="h-4 w-4" />
        Chat with agent
      </Button>
    </div>
  );
}
```

**UI/UX Requirements**:
- Horizontal layout (not vertical dropdown)
- Position above or below selected text
- Auto-close when clicking outside
- Smooth fade-in/out animation
- Mobile-responsive positioning

**Dependencies**: 
- Shadcn UI Button component
- lucide-react icons
- React Portal for absolute positioning

---

#### Task 3.4: Implement Text Highlighting System
**File**: `frontend/components/Canvas/TextRenderer.tsx`

**Actions**:
1. Add state to track highlighted text ranges
2. Apply yellow background color to highlighted text
3. Persist highlight until user clears or selects new text
4. Support multiple highlights (future enhancement)

**Implementation Pattern**:
```tsx
const [highlights, setHighlights] = useState<Array<{
  id: string;
  range: { start: number; end: number };
  color: string;
}>>([]);

const addHighlight = (text: string, range: { start: number; end: number }) => {
  const newHighlight = {
    id: `highlight-${Date.now()}`,
    range,
    color: '#FFEB3B' // Yellow
  };
  setHighlights(prev => [...prev, newHighlight]);
};

// Apply highlights to BlockNote editor
useEffect(() => {
  highlights.forEach(highlight => {
    editor.addMark(highlight.range, {
      type: 'backgroundColor',
      attrs: { color: highlight.color }
    });
  });
}, [highlights, editor]);
```

**Technical Considerations**:
- Use BlockNote's text decoration/mark API
- Yellow color: `#FFEB3B` or `bg-yellow-200`
- Handle overlapping highlights
- Provide clear highlight functionality (optional)

**Dependencies**: BlockNote text marking API

---

#### Task 3.5: Integrate Custom Menu with TextRenderer
**File**: `frontend/components/Canvas/TextRenderer.tsx`

**Actions**:
1. Import and render `ArtifactContextMenu` conditionally
2. Calculate menu position based on text selection
3. Handle "Chat with agent" button click
4. Connect to chat input focus mechanism

**Integration Pattern**:
```tsx
import { ArtifactContextMenu } from './ArtifactContextMenu';

export function TextRenderer({ markdown, isStreaming, onUpdate }: TextRendererProps) {
  const [showContextMenu, setShowContextMenu] = useState(false);
  const [menuPosition, setMenuPosition] = useState({ x: 0, y: 0 });
  
  const handleTextSelection = (selection: Selection) => {
    if (selection.text.trim()) {
      const rect = selection.getBoundingClientRect();
      setMenuPosition({
        x: rect.left + rect.width / 2,
        y: rect.top - 40 // Position above selection
      });
      setShowContextMenu(true);
    }
  };
  
  const handleChatWithAgent = (text: string) => {
    // Add highlight
    addHighlight(text, selectedText.range);
    
    // Focus chat input (via callback prop)
    onChatWithAgentClick?.(text);
    
    // Close menu
    setShowContextMenu(false);
  };
  
  return (
    <div className="relative h-full w-full overflow-auto">
      {/* BlockNoteView */}
      
      {showContextMenu && selectedText && (
        <ArtifactContextMenu
          selectedText={selectedText.text}
          position={menuPosition}
          onChatWithAgent={handleChatWithAgent}
          onClose={() => setShowContextMenu(false)}
        />
      )}
    </div>
  );
}
```

**Dependencies**: Task 3.2, Task 3.3, Task 3.4

---

#### Task 3.6: Add Chat Input Focus Mechanism
**Files**: 
- `frontend/components/Canvas/TextRenderer.tsx`
- `frontend/components/Canvas/CanvasChatContainer.tsx`
- `frontend/contexts/CanvasContext.tsx`

**Actions**:
1. Add new prop to `TextRenderer`: `onChatWithAgentClick: (text: string) => void`
2. Update `CanvasContext` to provide chat input ref
3. Pass ref through component hierarchy
4. Focus chat input when "Chat with agent" is clicked

**Implementation Pattern**:

**Step 1**: Update CanvasContext
```tsx
// frontend/contexts/CanvasContext.tsx
interface CanvasContextValue {
  // ... existing fields
  chatInputRef: RefObject<ChatInputRef> | null;
  setChatInputRef: (ref: RefObject<ChatInputRef>) => void;
  selectedTextForChat: string | null;
  setSelectedTextForChat: (text: string | null) => void;
}
```

**Step 2**: Update CanvasChatContainer
```tsx
// frontend/components/Canvas/CanvasChatContainer.tsx
const chatInputRef = useRef<ChatInputRef>(null);
const { setChatInputRef } = useCanvas();

useEffect(() => {
  setChatInputRef(chatInputRef);
}, [setChatInputRef]);
```

**Step 3**: Update ArtifactRenderer
```tsx
// frontend/components/Canvas/ArtifactRenderer.tsx
const { chatInputRef, setSelectedTextForChat } = useCanvas();

const handleChatWithAgent = (text: string) => {
  setSelectedTextForChat(text);
  chatInputRef?.current?.focus();
};

<TextRenderer
  markdown={displayContent.fullMarkdown}
  isStreaming={isStreaming}
  onUpdate={(newMarkdown) => onArtifactUpdate(newMarkdown, artifact.currentIndex)}
  onChatWithAgentClick={handleChatWithAgent}
/>
```

**Dependencies**: 
- Existing `ChatInputRef` interface (already implemented)
- CanvasContext updates
- Component prop threading

---

#### Task 3.7: Testing and Polish
**Files**: All modified components

**Actions**:
1. Test text selection and menu appearance
2. Test highlight persistence across edits
3. Test focus behavior on different devices
4. Test edge cases:
   - Empty selection
   - Menu positioning at viewport edges
   - Multiple rapid selections
   - Streaming while menu is open
5. Add keyboard shortcuts (optional):
   - Escape to close menu
   - Ctrl+Shift+C to open "Chat with agent" directly
6. Responsive design testing (mobile/tablet)

**UI/UX Validation**:
- Menu appears within 200ms of selection
- Highlight is visible and doesn't overlap text
- Chat input focuses smoothly
- No layout shifts when menu appears
- Menu disappears when clicking outside

---

### 4. Optional Enhancements (Future Iterations)

#### 4.1: Multiple Highlights Support
- Allow users to highlight multiple text sections
- Different colors for different highlight types
- Clear individual or all highlights button

#### 4.2: Pre-fill Chat Input with Context
- When focusing chat input, add prefix like: "Regarding: [selected text]..."
- User can edit or remove prefix

#### 4.3: Highlight Management Panel
- Show list of all highlights in sidebar
- Click to jump to highlight
- Delete individual highlights

#### 4.4: AG-UI Event Integration
- Emit `TEXT_SELECTED` event to backend
- Backend can suggest relevant prompts
- Track user interaction patterns

---

## Testing Strategy

### Unit Tests
- Text selection detection
- Menu positioning calculation
- Highlight state management

### Integration Tests
- End-to-end flow: select text → menu → highlight → focus chat
- Context menu close on outside click
- Highlight persistence during streaming

### Manual Testing
- Cross-browser compatibility (Chrome, Firefox, Safari)
- Mobile responsiveness
- Accessibility (keyboard navigation)

---

## Dependencies

### External Libraries
- `@blocknote/react` - Already installed
- `@blocknote/shadcn` - Already installed
- No new dependencies required

### Internal Components
- `ChatInput` with `ChatInputRef` interface ✅ (already exists)
- `CanvasContext` - Needs updates for chat input ref
- Shadcn UI components - Already available

---

## Rollout Plan

### Phase 1: Core Functionality (MVP)
- Disable default context menu ✅
- Add custom horizontal menu ✅
- Text highlighting ✅
- Chat input focus ✅

### Phase 2: Polish
- Animations and transitions
- Edge case handling
- Mobile optimization

### Phase 3: Enhancements
- Multiple highlights
- Pre-fill chat input
- Highlight management

---

## Technical Notes

### BlockNote API Research Required
- **Context menu disable**: Check official docs for proper API
- **Text selection API**: Explore `editor.getSelection()` and selection events
- **Text decoration API**: Investigate mark/decoration system for highlights

### Useful BlockNote Resources
- Official docs: https://www.blocknotejs.org/
- API reference: https://www.blocknotejs.org/docs/editor-basics/selection
- Examples: https://github.com/TypeCellOS/BlockNote/tree/main/examples

---

## Success Criteria

- ✅ Default BlockNote context menu is fully disabled
- ✅ Custom horizontal menu appears on text selection
- ✅ "Chat with agent" button is clearly visible and clickable
- ✅ Selected text is highlighted in yellow when clicked
- ✅ Chat input receives focus immediately
- ✅ No layout shifts or visual glitches
- ✅ Works on mobile and desktop
- ✅ Graceful handling of edge cases

---

## Knowledge Base Updates

After implementation, update:
- `/.docs/2-knowledge-base/frontend-patterns.md` - Add custom context menu pattern
- `/.docs/2-knowledge-base/blocknote-integration.md` - Document BlockNote customization techniques
- `/.docs/2-knowledge-base/canvas-features.md` - Document artifact panel interactions
