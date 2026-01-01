# Mobile Support Implementation

## Overview

The AgentKit frontend now supports mobile devices with responsive layouts, touch gestures, and adaptive navigation patterns. This document outlines the mobile-specific patterns and components implemented.

## Mobile Breakpoints

Standard breakpoints defined in `hooks/useMediaQuery.ts`:

- **Mobile**: < 768px
- **Tablet**: 768px - 1023px  
- **Desktop**: ≥ 1024px

## Core Hooks

### useMediaQuery

Detects viewport breakpoints and provides responsive utilities:

```typescript
import { useIsMobile, useIsTablet, useIsDesktop, useBreakpoints } from '@/hooks/useMediaQuery';

// Individual breakpoint checks
const isMobile = useIsMobile();
const isTablet = useIsTablet();
const isDesktop = useIsDesktop();

// Or get all at once
const { isMobile, isTablet, isDesktop, isMobileOrTablet } = useBreakpoints();
```

**Features**:
- Server-side safe (returns false during SSR to avoid hydration mismatch)
- Uses modern `matchMedia` API with fallback for older browsers
- Re-renders only when breakpoint changes

### useSwipeGesture

Detects and handles swipe gestures with configurable thresholds:

```typescript
import { useSwipeGesture, useHorizontalSwipe, useVerticalSwipe } from '@/hooks/useSwipeGesture';

// Full control
const swipeHandlers = useSwipeGesture({
  threshold: 50, // Min pixels to trigger swipe
  velocityThreshold: 0.3, // Min velocity (px/ms)
  onSwipe: (direction, distance, velocity) => {
    console.log(`Swiped ${direction}`);
  },
  onSwiping: (deltaX, deltaY) => {
    // Track swipe in progress
  },
  onSwipeStart: (x, y) => {
    // Swipe started
  },
  onSwipeEnd: () => {
    // Swipe ended
  },
});

// Apply to element
<div {...swipeHandlers}>Swipeable content</div>

// Simplified horizontal swipes
const handlers = useHorizontalSwipe(
  () => console.log('Swiped left'),
  () => console.log('Swiped right')
);
```

## Mobile Navigation Pattern

### Sidebar → Mobile Drawer

On mobile, the sidebar transforms into an overlay drawer:

**Desktop Behavior** (≥ 768px):
- Fixed sidebar with collapse toggle
- 64px collapsed, 256px expanded
- Persistent across page views

**Mobile Behavior** (< 768px):
- Hidden by default
- Opens as overlay drawer from left
- Backdrop overlay dims background
- Swipe left to close
- Auto-closes after thread selection
- Escape key to close
- Prevents body scroll when open

**Implementation** in `Sidebar.tsx`:
```typescript
const isMobile = useIsMobile();

// Swipe gesture for closing
const swipeHandlers = useHorizontalSwipe(
  () => {
    if (isMobile && isMobileOpen && onCloseMobile) {
      onCloseMobile();
    }
  },
  undefined,
  { threshold: 75 }
);

// Conditional rendering
if (isMobile) {
  return (
    <>
      {/* Backdrop */}
      {isMobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50"
          onClick={onCloseMobile}
        />
      )}
      
      {/* Drawer */}
      <aside
        {...swipeHandlers}
        className={cn(
          "fixed inset-y-0 left-0 z-50 w-64",
          isMobileOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        {/* Drawer content */}
      </aside>
    </>
  );
}
```

### Header with Hamburger Menu

The Header component adapts to mobile with:

**Mobile Changes**:
- Hamburger menu button (top-left)
- Selectors stacked vertically
- Auto height instead of fixed 64px
- Full-width selectors

**Desktop Behavior**:
- No hamburger menu
- Horizontal selector layout
- Fixed 64px height

**Implementation** in `Header.tsx`:
```typescript
const isMobile = useIsMobile();

return (
  <header className="border-b">
    <div className={cn(
      "flex items-center px-4 md:px-6",
      isMobile ? "flex-col gap-2 py-3 min-h-16" : "h-16 gap-4"
    )}>
      {isMobile ? (
        <>
          <div className="flex justify-between w-full">
            <Button onClick={onMenuClick}>
              <Menu className="h-5 w-5" />
            </Button>
          </div>
          <div className="flex flex-col gap-2 w-full">
            <AgentSelector />
            <ProviderSelector />
            <ModelSelector />
          </div>
        </>
      ) : (
        <>
          <AgentSelector />
          <ProviderSelector />
          <ModelSelector />
        </>
      )}
    </div>
  </header>
);
```

### Mobile Tab Navigation

For Chat/Canvas switching on mobile, use the `MobileTabNavigation` component:

**Features**:
- Two tabs: Chat and Canvas
- Swipe gestures to switch tabs
- Badge indicator for new canvas content
- Only shown on mobile when canvas is active

**Implementation**:
```typescript
import { MobileTabNavigation, MobileTab } from '@/components/MobileTabNavigation';

const [mobileTab, setMobileTab] = useState<MobileTab>('chat');

// Show tabs only on mobile when canvas is active
{isMobile && canvasModeActive && (
  <MobileTabNavigation
    activeTab={mobileTab}
    onTabChange={setMobileTab}
    showCanvasBadge={canvasModeActive && mobileTab === 'chat'}
  />
)}
```

## Mobile Layout Pattern in ChatApp

The `ChatApp` component uses conditional rendering for mobile:

**Mobile** (< 768px):
- Tab-based navigation
- Single view (either chat or canvas)
- State preserved when switching tabs

**Desktop** (≥ 768px):
- Side-by-side layout
- Resizable panels
- Simultaneous chat + canvas view

```typescript
const isMobile = useIsMobile();
const [mobileTab, setMobileTab] = useState<MobileTab>('chat');

return (
  <Layout onMenuClick={toggleMobileDrawer}>
    {/* Mobile tabs */}
    {isMobile && canvasModeActive && (
      <MobileTabNavigation
        activeTab={mobileTab}
        onTabChange={setMobileTab}
      />
    )}

    {/* Content */}
    <div className={isMobile ? "h-full" : "flex h-full"}>
      {isMobile ? (
        /* Mobile: Show only active tab */
        <>
          {mobileTab === 'chat' && <ChatContainer />}
          {mobileTab === 'canvas' && <ArtifactPanel />}
        </>
      ) : (
        /* Desktop: Side-by-side */
        <>
          <ChatContainer />
          {canvasModeActive && (
            <>
              <ResizableDivider />
              <ArtifactPanel />
            </>
          )}
        </>
      )}
    </div>
  </Layout>
);
```

## Responsive Selector Components

All selector components (AgentSelector, ProviderSelector, ModelSelector) are mobile-responsive:

**Changes**:
- Full-width on mobile (`w-full md:w-auto`)
- Space-between layout on mobile (`justify-between md:justify-start`)
- Icon and text wrapped in flex container
- Chevron always visible on mobile

```typescript
<Button className="gap-2 w-full md:w-auto justify-between md:justify-start">
  <div className="flex items-center gap-2">
    <Icon className="h-4 w-4" />
    <span className="hidden sm:inline">
      {label}
    </span>
  </div>
  <ChevronDown className="h-4 w-4" />
</Button>
```

## Mobile State Management

The `useSidebar` hook manages both desktop collapse state and mobile drawer state:

```typescript
export function useSidebar() {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [isMobileOpen, setIsMobileOpen] = useState(false);
  
  return {
    // Desktop collapse
    isCollapsed,
    toggleCollapse,
    setCollapsed,
    
    // Mobile drawer
    isMobileOpen,
    openMobileDrawer,
    closeMobileDrawer,
    toggleMobileDrawer,
  };
}
```

## Auto Canvas Tab Switching

When an artifact is detected on mobile, automatically switch to canvas tab:

```typescript
const handleArtifactDetected = useCallback((message: Message) => {
  activateCanvas(message);
  
  if (isMobile) {
    setMobileTab('canvas'); // Switch to canvas tab
  } else {
    setCollapsed(true); // Collapse sidebar on desktop
  }
}, [activateCanvas, isMobile, setCollapsed]);
```

## Mobile UX Best Practices

### Touch Targets
- Minimum 44x44px for all interactive elements (iOS/Android guidelines)
- Adequate spacing between touch targets (8px minimum)

### Gesture Conflicts
- Use threshold detection (50-75px) to avoid conflicts with scroll
- Test swipe gestures on real devices
- Provide visual feedback during gestures

### Performance
- Use `useMediaQuery` hook to avoid unnecessary re-renders
- Lazy load heavy components (already implemented with dynamic imports)
- Prevent body scroll when drawer is open

### Accessibility
- Keyboard support (Escape to close drawer)
- Proper ARIA labels for mobile-only elements
- Focus management when opening/closing drawer

## Testing Checklist

- [ ] Test sidebar drawer on mobile (< 768px)
- [ ] Test hamburger menu toggles drawer
- [ ] Test swipe gestures (left/right)
- [ ] Test tab navigation on mobile
- [ ] Test auto-switch to canvas tab when artifact detected
- [ ] Test selector full-width layout on mobile
- [ ] Test header vertical stacking on mobile
- [ ] Test backdrop closes drawer
- [ ] Test escape key closes drawer
- [ ] Test body scroll lock when drawer open
- [ ] Test auto-close drawer after thread selection
- [ ] Test portrait and landscape orientations
- [ ] Test on actual iOS and Android devices

## Future Enhancements (Phase 2+)

- **Pull-to-refresh**: Refresh chat history
- **Touch optimizations**: Larger touch targets for A2UI components
- **PWA support**: Install to home screen
- **Bottom navigation**: Alternative mobile navigation pattern
- **Swipe tab switching**: Between chat and canvas tabs

## Related Files

- `frontend/hooks/useMediaQuery.ts` - Breakpoint detection
- `frontend/hooks/useSwipeGesture.ts` - Touch gesture handling
- `frontend/hooks/useSidebar.ts` - Sidebar/drawer state management
- `frontend/components/Sidebar.tsx` - Responsive sidebar/drawer
- `frontend/components/Header.tsx` - Responsive header with hamburger
- `frontend/components/MobileTabNavigation.tsx` - Mobile tab navigation
- `frontend/components/ChatApp.tsx` - Mobile layout orchestration
- `frontend/components/Layout.tsx` - Layout with menu handler
- `frontend/components/AgentSelector.tsx` - Responsive selector
- `frontend/components/ProviderSelector.tsx` - Responsive selector
- `frontend/components/ModelSelector.tsx` - Responsive selector
