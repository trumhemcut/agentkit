# Implementation Plan: Mobile Support

**Requirement**: [027-support-mobile.md](../.0-requirements/027-support-mobile.md)  
**Status**: Draft  
**Priority**: Medium  
**Scope**: Frontend-focused responsive design and mobile UX improvements

## Overview

Transform the AgentKit application to be fully responsive and mobile-friendly with adaptive layouts, touch gestures, and optimized mobile navigation patterns. This is primarily a frontend initiative with minimal backend changes.

## Architecture Analysis

Current state:
- Fixed-width sidebar (64px collapsed, 256px expanded)
- Fixed-height header (64px) with horizontal selectors
- Side-by-side chat/canvas layout
- Desktop-first responsive design
- No mobile-specific navigation patterns

Target state:
- Adaptive sidebar (hidden on mobile, overlay drawer)
- Responsive header with vertical stacking on mobile
- Tab-based navigation for chat/canvas on mobile
- Touch gesture support (swipe, pull-to-refresh)
- Optional PWA capabilities for install-to-home-screen

---

## Implementation Tasks

### Phase 1: Responsive Foundation 🎯

#### 1.1 Mobile Sidebar Drawer
**Owner**: Frontend Agent  
**Priority**: High  
**Dependencies**: None

**Tasks**:
- [ ] Add mobile breakpoint detection hook (`useMediaQuery`)
  - Create `hooks/useMediaQuery.ts` with standard breakpoints (sm: 640px, md: 768px, lg: 1024px)
  - Export `isMobile`, `isTablet`, `isDesktop` helpers
  
- [ ] Update `Sidebar.tsx` with mobile overlay behavior
  - Hide sidebar completely on mobile (< 768px)
  - Add overlay backdrop when open on mobile
  - Implement slide-in animation from left
  - Add `isOpen` state for mobile drawer control
  
- [ ] Add hamburger menu button to `Header.tsx`
  - Show only on mobile breakpoints
  - Position top-left corner
  - Toggle sidebar drawer open/close
  - Use `Menu` icon from lucide-react
  
- [ ] Implement swipe gesture support
  - Add touch event handlers to sidebar
  - Swipe right to open (from left edge)
  - Swipe left to close
  - Use threshold (e.g., 50px swipe distance)
  - Add visual feedback during swipe
  
**Files to modify**:
- `frontend/components/Sidebar.tsx`
- `frontend/components/Header.tsx`
- `frontend/hooks/useSidebar.ts`
- Create: `frontend/hooks/useMediaQuery.ts`
- Create: `frontend/hooks/useSwipeGesture.ts`

**Protocol Impact**: None (frontend-only)

---

#### 1.2 Responsive Header Layout
**Owner**: Frontend Agent  
**Priority**: High  
**Dependencies**: Task 1.1 (mobile detection hook)

**Tasks**:
- [ ] Refactor `Header.tsx` for responsive layout
  - Stack AgentSelector, ProviderSelector, ModelSelector vertically on mobile
  - Reduce height on mobile (auto height instead of fixed 64px)
  - Add hamburger menu button (top-left, mobile only)
  - Maintain horizontal layout on desktop (>= 768px)
  
- [ ] Update individual selector components
  - `AgentSelector.tsx`: Full-width on mobile, compact on desktop
  - `ProviderSelector.tsx`: Full-width on mobile, compact on desktop
  - `ModelSelector.tsx`: Full-width on mobile, compact on desktop
  - Add responsive padding/margins
  
- [ ] Test header behavior across breakpoints
  - Mobile portrait (320px - 480px)
  - Mobile landscape (481px - 767px)
  - Tablet (768px - 1023px)
  - Desktop (>= 1024px)

**Files to modify**:
- `frontend/components/Header.tsx`
- `frontend/components/AgentSelector.tsx`
- `frontend/components/ProviderSelector.tsx`
- `frontend/components/ModelSelector.tsx`

**Protocol Impact**: None (frontend-only)

---

#### 1.3 Chat/Canvas Tab Navigation
**Owner**: Frontend Agent  
**Priority**: High  
**Dependencies**: Task 1.1 (mobile detection hook)

**Tasks**:
- [ ] Create `MobileTabNavigation.tsx` component
  - Two tabs: "Chat" and "Canvas"
  - Clear visual indicators for active tab
  - Smooth transition animations
  - Position: below header, above content
  - Use Shadcn UI `Tabs` component as base
  
- [ ] Update `ChatApp.tsx` for conditional layout
  - Desktop (>= 768px): Side-by-side chat + canvas (existing behavior)
  - Mobile (< 768px): Tab-based single view
  - Show only active panel on mobile
  - Preserve state when switching tabs
  
- [ ] Handle canvas mode activation on mobile
  - Auto-switch to "Canvas" tab when artifact detected
  - Show notification badge on "Canvas" tab when new artifact
  - Smooth tab transition animation
  
- [ ] Add swipe gesture for tab switching (optional enhancement)
  - Swipe left to switch from Chat → Canvas
  - Swipe right to switch from Canvas → Chat
  - Visual feedback during swipe

**Files to modify**:
- `frontend/components/ChatApp.tsx`
- Create: `frontend/components/MobileTabNavigation.tsx`
- `frontend/hooks/useCanvasMode.ts` (minor updates for mobile tab switching)

**Protocol Impact**: None (frontend-only, state management internal)

---

### Phase 2: Touch Interactions ✨

#### 2.1 Swipe Gesture Infrastructure
**Owner**: Frontend Agent  
**Priority**: Medium  
**Dependencies**: Phase 1 complete

**Tasks**:
- [ ] Create `useSwipeGesture.ts` hook
  - Detect touch start, move, end events
  - Calculate swipe direction (left, right, up, down)
  - Calculate swipe distance and velocity
  - Configurable thresholds
  - Return swipe state and handlers
  
- [ ] Apply swipe gestures to sidebar
  - Swipe right from left edge to open sidebar
  - Swipe left on open sidebar to close
  - Add visual feedback (follow finger during swipe)
  
- [ ] Apply swipe gestures to tabs
  - Swipe left/right to switch between Chat and Canvas
  - Smooth transition with finger tracking
  - Snap to nearest tab on release

**Files to modify**:
- Create: `frontend/hooks/useSwipeGesture.ts`
- `frontend/components/Sidebar.tsx` (apply swipe gestures)
- `frontend/components/MobileTabNavigation.tsx` (apply swipe gestures)

**Protocol Impact**: None (frontend-only)

---

#### 2.2 Pull-to-Refresh
**Owner**: Frontend Agent  
**Priority**: Low  
**Dependencies**: Task 2.1 (swipe gesture hook)

**Tasks**:
- [ ] Implement pull-to-refresh for chat container
  - Detect pull gesture from top of chat scroll container
  - Show loading indicator while refreshing
  - Trigger thread refresh on release
  - Add spring animation for feedback
  
- [ ] Add visual feedback
  - Loading spinner appears during pull
  - Success animation on refresh complete
  - Works on chat history list

**Files to modify**:
- `frontend/components/ChatContainer.tsx`
- `frontend/hooks/useChatThreads.ts` (expose refresh function)

**Protocol Impact**: None (frontend-only)

---

### Phase 3: Mobile Optimizations 📱

#### 3.1 Responsive Component Adjustments
**Owner**: Frontend Agent  
**Priority**: Medium  
**Dependencies**: Phase 1 complete

**Tasks**:
- [ ] Update message bubbles for mobile
  - `UserMessageBubble.tsx`: Reduce padding on mobile
  - `AgentMessageBubble.tsx`: Reduce padding on mobile
  - Adjust max-width for mobile screens
  - Increase font size for readability (16px minimum)
  
- [ ] Update artifact panel for mobile
  - `ArtifactPanel.tsx`: Full-screen on mobile
  - Adjust toolbar for mobile (stack buttons if needed)
  - Optimize code editor for mobile touch
  
- [ ] Update A2UI components for mobile
  - `A2UIButton.tsx`: Larger touch targets (min 44x44px)
  - `A2UITextInput.tsx`: Adjust input height for mobile keyboards
  - `A2UIOTPInput.tsx`: Optimize for mobile input
  - `A2UIBarChart.tsx`: Responsive chart sizing
  
- [ ] Update chat input area
  - Adjust height for mobile keyboards
  - Add auto-resize textarea behavior
  - Optimize send button for mobile touch

**Files to modify**:
- `frontend/components/UserMessageBubble.tsx`
- `frontend/components/AgentMessageBubble.tsx`
- `frontend/components/ArtifactPanel.tsx`
- `frontend/components/A2UI/*.tsx` (all A2UI components)
- `frontend/components/ChatContainer.tsx`

**Protocol Impact**: None (frontend-only)

---

#### 3.2 Touch Target Optimization
**Owner**: Frontend Agent  
**Priority**: Medium  
**Dependencies**: None

**Tasks**:
- [ ] Audit all interactive elements for touch target size
  - Ensure minimum 44x44px touch targets (Apple/Android guidelines)
  - Add adequate spacing between touch targets (min 8px)
  
- [ ] Update button components
  - Increase button size on mobile (Shadcn UI size variants)
  - Add touch-friendly spacing
  - Test with actual mobile devices
  
- [ ] Update icon buttons
  - Increase icon button size on mobile
  - Add visible focus states for accessibility
  - Test tap accuracy

**Files to modify**:
- All button-containing components
- `frontend/components/ui/button.tsx` (may need mobile variants)

**Protocol Impact**: None (frontend-only)

---

### Phase 4: Progressive Web App (PWA) 🚀

#### 4.1 PWA Configuration
**Owner**: Frontend Agent  
**Priority**: Low (Nice to Have)  
**Dependencies**: Phase 1-3 complete

**Tasks**:
- [ ] Create PWA manifest.json
  - App name, icons, theme colors
  - Display mode: standalone
  - Orientation: portrait preferred
  - Icon sizes: 192x192, 512x512
  
- [ ] Create service worker
  - Cache static assets
  - Offline fallback page
  - Network-first strategy for API calls
  
- [ ] Add install prompt
  - Detect if app is installable
  - Show custom install banner
  - Handle install event
  
- [ ] Update Next.js configuration
  - Enable PWA support (next-pwa plugin)
  - Configure caching strategies
  - Update `next.config.ts`

**Files to modify**:
- Create: `frontend/public/manifest.json`
- Create: `frontend/public/sw.js` (service worker)
- Create: `frontend/components/InstallPrompt.tsx`
- `frontend/next.config.ts`
- `frontend/app/layout.tsx` (add manifest link)

**Dependencies**:
- Install `next-pwa` package

**Protocol Impact**: None (frontend-only)

---

#### 4.2 Bottom Navigation Bar (Alternative Pattern)
**Owner**: Frontend Agent  
**Priority**: Low (Nice to Have)  
**Dependencies**: Phase 1 complete

**Tasks**:
- [ ] Create `BottomNavigationBar.tsx` component
  - Show on mobile only (< 768px)
  - Icons for: New Chat, Thread List, Settings, Canvas
  - Fixed position at bottom
  - Active state indicators
  
- [ ] Integrate with existing navigation
  - Make optional (feature flag or setting)
  - Alternative to hamburger + sidebar pattern
  - Test user preference
  
- [ ] Add smooth transitions
  - Slide up from bottom on mount
  - Icon animations on tap
  - Badge for canvas notifications

**Files to modify**:
- Create: `frontend/components/BottomNavigationBar.tsx`
- `frontend/components/ChatApp.tsx` (conditional rendering)

**Protocol Impact**: None (frontend-only)

---

## Testing Strategy

### Manual Testing Checklist
- [ ] Test on actual mobile devices (iOS + Android)
- [ ] Test all breakpoints (320px, 375px, 414px, 768px, 1024px)
- [ ] Test portrait and landscape orientations
- [ ] Test touch gestures (swipe, tap, pull-to-refresh)
- [ ] Test sidebar drawer on mobile
- [ ] Test tab navigation on mobile
- [ ] Test header responsiveness
- [ ] Test A2UI components on mobile
- [ ] Test chat input with mobile keyboard
- [ ] Test artifact panel full-screen on mobile

### Browser Testing
- [ ] Chrome (Android)
- [ ] Safari (iOS)
- [ ] Firefox (Android)
- [ ] Samsung Internet
- [ ] Edge (mobile)

### Performance Testing
- [ ] Measure First Contentful Paint (FCP) on mobile
- [ ] Measure Time to Interactive (TTI) on mobile
- [ ] Test touch response latency
- [ ] Test scroll performance
- [ ] Test animation smoothness (60fps target)

---

## Dependencies

### Frontend Dependencies
**Existing**:
- `lucide-react` - Icons (Menu icon for hamburger)
- `@radix-ui/react-tabs` - Tab component base (via Shadcn UI)
- `tailwindcss` - Responsive utilities

**New** (for PWA):
- `next-pwa` - PWA support for Next.js (optional, Phase 4 only)

**Backend Dependencies**: None (no backend changes required)

---

## Rollout Plan

### Phase 1: Foundation (Week 1)
- Implement mobile sidebar drawer
- Implement responsive header
- Implement chat/canvas tab navigation
- **Goal**: Basic mobile usability

### Phase 2: Touch Interactions (Week 2)
- Implement swipe gestures
- Implement pull-to-refresh
- **Goal**: Native-like mobile experience

### Phase 3: Optimization (Week 3)
- Responsive component adjustments
- Touch target optimization
- **Goal**: Polished mobile UX

### Phase 4: PWA (Optional, Week 4)
- PWA configuration
- Bottom navigation (alternative pattern)
- **Goal**: Install-to-home-screen capability

---

## Success Criteria

### Must Have ✅
- [x] Sidebar works as drawer on mobile (< 768px)
- [x] Header stacks vertically on mobile
- [x] Chat/Canvas switch via tabs on mobile
- [x] All touch targets minimum 44x44px
- [x] Responsive layouts tested on real devices

### Nice to Have ⭐
- [ ] Swipe gestures for navigation
- [ ] Pull-to-refresh functionality
- [ ] PWA install-to-home-screen
- [ ] Bottom navigation bar (alternative)

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Touch gesture conflicts with scroll | High | Use threshold detection, test on devices |
| PWA service worker cache issues | Medium | Careful cache strategy, versioning |
| Mobile performance degradation | High | Lazy load components, optimize bundle size |
| iOS Safari-specific bugs | Medium | Test early on iOS devices, use -webkit- prefixes |
| Keyboard covering input on mobile | High | Use viewport units, adjust scroll position |

---

## References

### Design Guidelines
- [Apple Human Interface Guidelines - Touch Targets](https://developer.apple.com/design/human-interface-guidelines/layout)
- [Material Design - Touch Targets](https://m3.material.io/foundations/interaction/states/applying-states)
- [Web.dev - Mobile Web Best Practices](https://web.dev/mobile/)

### Technical References
- [Next.js Responsive Design](https://nextjs.org/docs/app/building-your-application/styling/responsive-design)
- [Tailwind CSS Responsive Design](https://tailwindcss.com/docs/responsive-design)
- [PWA Documentation](https://web.dev/progressive-web-apps/)

### Project Context
- Backend Agent Guide: [backend.agent.md](../../.github/agents/backend.agent.md) - Not applicable (no backend changes)
- Frontend Agent Guide: [frontend.agent.md](../../.github/agents/frontend.agent.md) - **Primary reference for implementation**
- AG-UI Protocol: Backend AG-UI integration patterns (no protocol changes needed)

---

## Notes

- **Frontend-focused**: This is primarily a frontend initiative with zero backend changes
- **Existing patterns**: Leverage existing Shadcn UI components and Tailwind responsive utilities
- **Progressive enhancement**: Desktop experience remains unchanged, mobile gets adaptive improvements
- **Testing priority**: Real device testing is critical (not just browser DevTools)
- **Performance**: Monitor bundle size increases from new mobile features
