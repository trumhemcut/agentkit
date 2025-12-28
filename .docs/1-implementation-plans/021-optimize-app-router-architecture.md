# Implementation Plan: Optimize App Router Architecture

**Status**: Ready for Implementation  
**Priority**: High (Performance Optimization)  
**Estimated Effort**: Medium (2-3 PRs)  
**Based on**: [0-requirements/021-fe-misusing-approuter.md](../0-requirements/021-fe-misusing-approuter.md)

## Problem Analysis

### Current State
The entire application is client-side rendered due to `'use client'` directive at the root [page.tsx](../../frontend/app/page.tsx#L1), which misuses Next.js App Router capabilities:

**Evidence:**
- ✗ Root component marked as `'use client'`
- ✗ All 149 lines of `page.tsx` forced to client-side
- ✗ Heavy dependencies (Zustand, AG-UI, CodeMirror, BlockNote) shipped in initial bundle
- ✗ No Server Components, no streaming, no progressive enhancement
- ✗ [layout.tsx](../../frontend/app/layout.tsx) is correctly a Server Component but wasted due to client child

**Bundle Impact:**
```
Current Dependencies Loaded Upfront:
- @blocknote/core + react + shadcn (~300KB)
- @codemirror/* packages (~250KB)
- @radix-ui components (~200KB)
- React + Next.js runtime
- AG-UI protocol handling
- Zustand stores
```

### Why This Matters
1. **Performance**: Slower initial page load, no static optimization
2. **SEO**: While chat may not need SEO, proper SSR/SSG enables future landing pages/docs
3. **Best Practices**: App Router designed for hybrid rendering
4. **User Experience**: No progressive enhancement, everything waits for full JS bundle

### Applicability Assessment
✅ **HIGHLY APPLICABLE** - This is a critical architectural optimization that:
- Leverages existing Next.js 14+ App Router features
- Does not break AG-UI streaming (can still use client components strategically)
- Reduces initial bundle size significantly
- Follows Next.js best practices
- Enables future SSR/SSG pages (docs, landing, marketing)

---

## Implementation Plan

### Phase 1: Refactor Root Layout (PR #1)
**Goal**: Convert page structure to proper Server/Client Component split

#### Backend Tasks
N/A - Frontend-only optimization

#### Frontend Tasks

##### Task 1.1: Extract Client Logic to Separate Component
**File**: `frontend/components/ChatApp.tsx` (NEW)
**Owner**: Frontend Agent

Create new component extracting all client-side logic from `page.tsx`:

```tsx
// components/ChatApp.tsx
'use client';

import { useRef, useCallback, useState } from 'react';
import { Layout } from '@/components/Layout';
import { Sidebar } from '@/components/Sidebar';
import { ChatContainer, ChatContainerRef } from '@/components/ChatContainer';
import { ArtifactPanel } from '@/components/ArtifactPanel';
import { ResizableDivider } from '@/components/ResizableDivider';
import { useChatThreads } from '@/hooks/useChatThreads';
import { useSidebar } from '@/hooks/useSidebar';
import { useCanvasMode } from '@/hooks/useCanvasMode';
import { Message } from '@/types/chat';
import { useCanvas } from '@/contexts/CanvasContext';

export function ChatApp() {
  // Move all HomeContent logic here (lines 15-147 from current page.tsx)
  const { ... } = useChatThreads();
  const { ... } = useSidebar();
  // ... rest of implementation
  
  return (
    <Layout sidebar={<Sidebar ... />}>
      {/* ... existing JSX */}
    </Layout>
  );
}
```

**Acceptance Criteria:**
- [ ] All hooks and state logic moved from `page.tsx`
- [ ] Component properly typed with TypeScript
- [ ] Maintains exact same behavior as current implementation
- [ ] No breaking changes to AG-UI streaming

##### Task 1.2: Simplify page.tsx to Server Component Wrapper
**File**: `frontend/app/page.tsx`
**Owner**: Frontend Agent

Convert to lightweight wrapper with dynamic import:

```tsx
// app/page.tsx
import { Suspense } from 'react';
import dynamic from 'next/dynamic';
import { CanvasProvider } from '@/contexts/CanvasContext';

// Dynamically import heavy client component
const ChatApp = dynamic(() => import('@/components/ChatApp').then(mod => ({ default: mod.ChatApp })), {
  loading: () => (
    <div className="flex items-center justify-center h-screen">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto mb-4"></div>
        <p className="text-gray-600">Loading AgentKit...</p>
      </div>
    </div>
  ),
  ssr: false, // AG-UI streaming requires client-side only
});

export default function Home() {
  return (
    <CanvasProvider>
      <Suspense fallback={<div>Initializing...</div>}>
        <ChatApp />
      </Suspense>
    </CanvasProvider>
  );
}
```

**Acceptance Criteria:**
- [ ] `'use client'` directive removed from page.tsx
- [ ] Dynamic import configured with proper loading state
- [ ] CanvasProvider still wraps ChatApp
- [ ] SSR explicitly disabled for AG-UI compatibility

##### Task 1.3: Verify layout.tsx Remains Server Component
**File**: `frontend/app/layout.tsx`
**Owner**: Frontend Agent

Ensure layout stays as Server Component (already correct, just verify):

```tsx
// app/layout.tsx (CURRENT - NO CHANGES NEEDED)
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
});

export const metadata: Metadata = {
  title: "AgentKit - Multi-Agent AI Assistant",
  description: "Agentic AI solution powered by LangGraph",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={inter.className}>
        {children}
      </body>
    </html>
  );
}
```

**Acceptance Criteria:**
- [ ] No `'use client'` directive
- [ ] Metadata export present (enables SEO)
- [ ] No state/effects/browser APIs used

---

### Phase 2: Add Loading & Error Boundaries (PR #2)
**Goal**: Implement App Router conventions for better UX

#### Frontend Tasks

##### Task 2.1: Create Global Loading UI
**File**: `frontend/app/loading.tsx` (NEW)
**Owner**: Frontend Agent

```tsx
// app/loading.tsx
export default function Loading() {
  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-50">
      <div className="text-center">
        <div className="inline-block animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600 mb-4"></div>
        <h2 className="text-xl font-semibold text-gray-800">Loading AgentKit</h2>
        <p className="text-gray-600 mt-2">Initializing AI agents...</p>
      </div>
    </div>
  );
}
```

**Acceptance Criteria:**
- [ ] Displays during initial page load
- [ ] Matches app design system (Tailwind + Shadcn UI)
- [ ] Provides visual feedback for loading state

##### Task 2.2: Create Global Error Boundary
**File**: `frontend/app/error.tsx` (NEW)
**Owner**: Frontend Agent

```tsx
// app/error.tsx
'use client'; // Error components must be Client Components

import { useEffect } from 'react';
import { Button } from '@/components/ui/button';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error('Application error:', error);
  }, [error]);

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-50">
      <div className="text-center max-w-md px-6">
        <div className="text-6xl mb-4">⚠️</div>
        <h2 className="text-2xl font-bold text-gray-800 mb-2">Something went wrong</h2>
        <p className="text-gray-600 mb-6">
          {error.message || 'An unexpected error occurred while loading the application.'}
        </p>
        <div className="flex gap-3 justify-center">
          <Button onClick={reset} variant="default">
            Try Again
          </Button>
          <Button onClick={() => window.location.href = '/'} variant="outline">
            Go Home
          </Button>
        </div>
        {error.digest && (
          <p className="text-xs text-gray-400 mt-4">Error ID: {error.digest}</p>
        )}
      </div>
    </div>
  );
}
```

**Acceptance Criteria:**
- [ ] Catches errors during rendering
- [ ] Provides reset functionality
- [ ] Logs errors for debugging
- [ ] Uses Shadcn UI Button component

---

### Phase 3: Optimization & Verification (PR #3)
**Goal**: Fine-tune and measure performance improvements

#### Frontend Tasks

##### Task 3.1: Add Component-Level Code Splitting
**File**: `frontend/components/ChatApp.tsx`
**Owner**: Frontend Agent

Optimize heavy components with dynamic imports:

```tsx
// In ChatApp.tsx
import dynamic from 'next/dynamic';

const ArtifactPanel = dynamic(() => import('@/components/ArtifactPanel').then(m => ({ default: m.ArtifactPanel })), {
  loading: () => <div className="flex items-center justify-center h-full">Loading Canvas...</div>,
});

const ResizableDivider = dynamic(() => import('@/components/ResizableDivider').then(m => ({ default: m.ResizableDivider })));
```

**Rationale:**
- `ArtifactPanel` contains BlockNote + CodeMirror (heavy)
- Only load when canvas mode activates
- Reduces initial bundle by ~300KB

**Acceptance Criteria:**
- [ ] Heavy components dynamically imported
- [ ] Loading states during lazy load
- [ ] No functionality regressions

##### Task 3.2: Performance Measurement
**Owner**: Frontend Agent

Add performance tracking to measure improvements:

```tsx
// In app/page.tsx or ChatApp.tsx
'use client';

import { useEffect } from 'react';

export function ChatApp() {
  useEffect(() => {
    // Log performance metrics
    if (typeof window !== 'undefined' && 'performance' in window) {
      const perfData = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      console.log('Performance Metrics:', {
        domContentLoaded: perfData.domContentLoadedEventEnd - perfData.domContentLoadedEventStart,
        loadComplete: perfData.loadEventEnd - perfData.loadEventStart,
        timeToInteractive: perfData.domInteractive - perfData.fetchStart,
      });
    }
  }, []);
  
  // ... rest of component
}
```

**Metrics to Track:**
- [ ] Initial bundle size (before/after)
- [ ] Time to First Byte (TTFB)
- [ ] First Contentful Paint (FCP)
- [ ] Time to Interactive (TTI)
- [ ] Largest Contentful Paint (LCP)

##### Task 3.3: Build Analysis
**Owner**: Frontend Agent

Run Next.js build analyzer:

```bash
# In frontend/
npm install -D @next/bundle-analyzer

# next.config.ts - add analyzer
const withBundleAnalyzer = require('@next/bundle-analyzer')({
  enabled: process.env.ANALYZE === 'true',
});

module.exports = withBundleAnalyzer({
  // ... existing config
});

# Run analysis
ANALYZE=true npm run build
```

**Compare:**
- [ ] Bundle size before optimization
- [ ] Bundle size after optimization
- [ ] Document findings in PR

---

## Testing Strategy

### Unit Tests
No new unit tests needed - functionality unchanged

### Integration Tests
**File**: `frontend/tests/app-router-optimization.test.tsx` (NEW)

```tsx
import { render, screen } from '@testing-library/react';
import Home from '@/app/page';

describe('App Router Optimization', () => {
  it('should render loading state initially', () => {
    render(<Home />);
    expect(screen.getByText(/Loading AgentKit/i)).toBeInTheDocument();
  });
  
  it('should not have "use client" directive in page.tsx', async () => {
    const pageContent = await import('fs').then(fs => 
      fs.promises.readFile('app/page.tsx', 'utf-8')
    );
    expect(pageContent).not.toContain("'use client'");
  });
});
```

### Manual Testing Checklist
- [ ] Page loads without errors
- [ ] Loading state displays briefly
- [ ] Chat functionality works identically
- [ ] Canvas mode activates correctly
- [ ] AG-UI streaming events work
- [ ] Thread management functions properly
- [ ] Sidebar collapse/expand works
- [ ] Artifact panel loads dynamically
- [ ] Error boundary catches intentional errors
- [ ] Performance metrics show improvement

---

## Protocol (AG-UI)
**No Changes Required** - AG-UI streaming protocol remains unchanged:
- Events still stream from backend via SSE
- Client-side event handlers in `ChatApp.tsx` (now in separate file)
- Canvas mode and artifact detection logic preserved

---

## Dependencies

### Between Tasks
1. **Task 1.1 → Task 1.2**: Must extract `ChatApp` before simplifying `page.tsx`
2. **Phase 1 → Phase 2**: Core refactor must work before adding error boundaries
3. **Phase 2 → Phase 3**: Stable structure needed before optimization

### External Dependencies
- No backend changes required
- No API contract changes
- No database migrations

---

## Rollback Plan

If issues arise:
```bash
# Revert commits in order
git revert <phase-3-commit>
git revert <phase-2-commit>
git revert <phase-1-commit>
```

Each phase is self-contained and revertible independently.

---

## Success Metrics

### Performance Improvements (Target)
- ✅ Initial bundle size: **-300KB** (from dynamic imports)
- ✅ First Contentful Paint: **-200ms** (from SSR shell)
- ✅ Time to Interactive: **-500ms** (from code splitting)
- ✅ Lighthouse Performance Score: **+10-15 points**

### Code Quality Improvements
- ✅ Proper Server/Client Component separation
- ✅ Follows Next.js App Router best practices
- ✅ Enables future SSR/SSG pages
- ✅ Better error handling with boundaries
- ✅ Progressive loading with Suspense

### Functional Requirements
- ✅ All existing functionality preserved
- ✅ AG-UI streaming works identically
- ✅ No breaking changes for users
- ✅ Improved perceived performance

---

## Future Enhancements

After this optimization, consider:
1. **SSR Pages**: Add server-rendered docs/landing pages
2. **Static Generation**: Generate marketing pages at build time
3. **Incremental Static Regeneration**: Cache agent responses for common queries
4. **Partial Prerendering (PPR)**: Next.js 14+ experimental feature
5. **React Server Actions**: For form submissions without API routes

---

## References

- [Next.js App Router Docs](https://nextjs.org/docs/app)
- [React Server Components](https://react.dev/reference/rsc/server-components)
- [Code Splitting Best Practices](https://nextjs.org/docs/app/building-your-application/optimizing/lazy-loading)
- [Performance Optimization](https://nextjs.org/docs/app/building-your-application/optimizing)
- **Requirement Doc**: [0-requirements/021-fe-misusing-approuter.md](../0-requirements/021-fe-misusing-approuter.md)

---

## Approval & Sign-off

- [ ] Frontend Agent reviewed
- [ ] Performance benchmarks documented
- [ ] Testing checklist completed
- [ ] Bundle analysis compared
- [ ] Production deployment approved
