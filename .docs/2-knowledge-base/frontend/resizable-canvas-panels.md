# Resizable Canvas Panels

## Overview
The canvas mode features a resizable divider that allows users to adjust the width ratio between the chat container and artifact panel. This provides flexibility for users to optimize their workspace based on their current task.

## Implementation

### Component: ResizableDivider

**Location**: `/frontend/components/ResizableDivider.tsx`

#### Features
- **Draggable Interface**: Click and drag to resize panels
- **Visual Feedback**: 
  - Hover state reveals grip indicator
  - Cursor changes to `col-resize` during interaction
  - Highlight effect on hover and drag
- **Constraints**:
  - Minimum left panel width: 20% (default, configurable)
  - Maximum left panel width: 70% (default, configurable)
  - Prevents extreme panel sizes for usability
- **Smooth Interaction**:
  - Real-time resize updates
  - Prevents text selection during drag
  - Returns cursor to normal after drag completes

#### Props

```typescript
interface ResizableDividerProps {
  onResize: (leftWidth: number) => void;  // Callback with new left panel width %
  minLeftWidth?: number;                   // Min left panel width % (default: 20)
  maxLeftWidth?: number;                   // Max left panel width % (default: 70)
  initialLeftWidth?: number;               // Initial width % (default: 33.33)
  className?: string;                      // Additional styling
}
```

#### Usage Example

```tsx
import { ResizableDivider } from '@/components/ResizableDivider';

function CanvasLayout() {
  const [chatPanelWidth, setChatPanelWidth] = useState(33.33);
  
  const handleResize = useCallback((leftWidth: number) => {
    setChatPanelWidth(leftWidth);
  }, []);
  
  return (
    <div className="flex h-full">
      {/* Left Panel */}
      <div style={{ width: `${chatPanelWidth}%` }}>
        <ChatContainer />
      </div>
      
      {/* Divider */}
      <ResizableDivider
        onResize={handleResize}
        minLeftWidth={20}
        maxLeftWidth={70}
        initialLeftWidth={chatPanelWidth}
      />
      
      {/* Right Panel */}
      <div style={{ width: `${100 - chatPanelWidth}%` }}>
        <ArtifactPanel />
      </div>
    </div>
  );
}
```

## Integration with Canvas Mode

### Page Implementation

**Location**: `/frontend/app/page.tsx`

The main page integrates the resizable divider into the canvas layout:

1. **State Management**: Tracks chat panel width percentage
2. **Dynamic Styling**: Applies inline styles for responsive width updates
3. **Conditional Rendering**: Only shows divider when canvas mode is active
4. **Layout Flow**:
   - Chat panel (left) with dynamic width
   - Resizable divider (center)
   - Artifact panel (right) with complementary width

```tsx
const [chatPanelWidth, setChatPanelWidth] = useState(33.33);

const handleResize = useCallback((leftWidth: number) => {
  setChatPanelWidth(leftWidth);
}, []);

// In render:
<div className="flex h-full">
  <div style={{ width: `${chatPanelWidth}%` }}>
    <ChatContainer canvasModeActive={true} />
  </div>
  
  <ResizableDivider
    onResize={handleResize}
    minLeftWidth={20}
    maxLeftWidth={70}
    initialLeftWidth={chatPanelWidth}
  />
  
  <div style={{ width: `${100 - chatPanelWidth}%` }}>
    <ArtifactPanel message={currentArtifactMessage} />
  </div>
</div>
```

## User Experience

### Interaction Flow

1. **Hover**: User hovers over the divider
   - Grip indicator becomes visible
   - Cursor changes to `col-resize`
   - Divider highlights with primary color

2. **Drag**: User clicks and drags
   - Cursor remains `col-resize`
   - Text selection is disabled
   - Panels resize in real-time
   - Width constrained between min/max values

3. **Release**: User releases mouse
   - Cursor returns to normal
   - Text selection re-enabled
   - New width persists for session

### Visual Design

- **Width**: 2px base (8px invisible hit area for easier grabbing)
- **Color**: Border color with hover state using primary color
- **Indicator**: Floating grip icon in rounded container
- **Transitions**: Smooth opacity transitions for visual feedback

### Accessibility

- **Cursor Feedback**: Clear visual indication of draggable area
- **Hit Area**: Extended invisible area (12px total) for easier interaction
- **Keyboard**: Could be extended with arrow key support
- **Screen Readers**: Consider adding ARIA labels in future iterations

## Technical Details

### Event Handling

The divider uses native mouse events for resize functionality:

```typescript
useEffect(() => {
  if (!isDragging) return;

  const handleMouseMove = (e: MouseEvent) => {
    const container = containerRef.current?.parentElement;
    const containerRect = container.getBoundingClientRect();
    const mouseX = e.clientX - containerRect.left;
    const containerWidth = containerRect.width;
    
    let leftWidthPercent = (mouseX / containerWidth) * 100;
    leftWidthPercent = Math.max(minLeftWidth, Math.min(maxLeftWidth, leftWidthPercent));
    
    onResize(leftWidthPercent);
  };

  const handleMouseUp = () => {
    setIsDragging(false);
    // Clean up cursor and selection styles
  };

  document.addEventListener('mousemove', handleMouseMove);
  document.addEventListener('mouseup', handleMouseUp);

  return () => {
    // Cleanup listeners
  };
}, [isDragging, minLeftWidth, maxLeftWidth, onResize]);
```

### Performance Considerations

- **Real-time Updates**: Resize calculations happen on every mouse move
- **Percentage-based**: Uses percentages for responsive scaling
- **No Debouncing**: Immediate feedback for smooth UX
- **Cleanup**: Proper event listener cleanup to prevent memory leaks

## Future Enhancements

### Potential Improvements

1. **Persistent Width**: Save user's preferred width to localStorage
2. **Keyboard Support**: Allow resize with arrow keys for accessibility
3. **Touch Support**: Add touch event handlers for mobile devices
4. **Double-click Reset**: Double-click divider to reset to default width
5. **Snap Points**: Predefined snap positions (25%, 33%, 50%, etc.)
6. **Animation**: Smooth transition when snapping to preset widths
7. **Width Presets**: Quick buttons for common layouts (1:1, 1:2, 1:3)

### Code Example for Persistent Width

```typescript
// Save to localStorage on resize
const handleResize = useCallback((leftWidth: number) => {
  setChatPanelWidth(leftWidth);
  localStorage.setItem('canvas-chat-width', leftWidth.toString());
}, []);

// Load from localStorage on mount
useEffect(() => {
  const savedWidth = localStorage.getItem('canvas-chat-width');
  if (savedWidth) {
    setChatPanelWidth(parseFloat(savedWidth));
  }
}, []);
```

## Related Files

- `/frontend/components/ResizableDivider.tsx` - Divider component
- `/frontend/app/page.tsx` - Main integration
- `/frontend/components/ChatContainer.tsx` - Left panel component
- `/frontend/components/ArtifactPanel.tsx` - Right panel component

## References

- [MDN: Mouse Events](https://developer.mozilla.org/en-US/docs/Web/API/MouseEvent)
- [React: useEffect Hook](https://react.dev/reference/react/useEffect)
- [Shadcn UI: Components](https://ui.shadcn.com/docs/components)
