# Frontend Architecture Review

**Date:** December 26, 2025  
**Reviewer:** Frontend Principal Engineer (AI)  
**Scope:** Next.js App Router + AG-UI + shadcn/ui Agentic AI Frontend  
**Project:** AgentKit Multi-Agent Chat Application

---

## 1. Architecture Summary

### Inferred Structure

**App Router Architecture:**
- **Framework:** Next.js 16.1.1 (App Router) with React 19.2.3
- **UI Library:** shadcn/ui (new-york style) with Tailwind CSS v4
- **State Management:** Zustand with localStorage persistence
- **AG-UI Integration:** Custom client implementation for SSE-based agent streaming
- **Type Safety:** TypeScript with strict mode enabled

**Component Organization:**
```
app/
  ├── layout.tsx (RootLayout, client-side only metadata)
  ├── page.tsx ('use client', main chat interface)
  └── globals.css (Tailwind v4 @theme syntax)

components/
  ├── ChatContainer.tsx (main orchestrator, handles AG-UI events)
  ├── MessageBubble.tsx, AgentMessageBubble.tsx, UserMessageBubble.tsx
  ├── ArtifactPanel.tsx (canvas mode panel)
  ├── Sidebar.tsx, Layout.tsx, Header.tsx
  ├── Canvas/ (CodeRenderer, TextRenderer, ArtifactContextMenu)
  └── ui/ (shadcn components: button, card, scroll-area, etc.)

stores/
  ├── agentStore.ts (agent selection with persist)
  └── modelStore.ts (LLM provider/model selection with persist)

hooks/
  ├── useAGUI.ts (AG-UI client wrapper)
  ├── useMessages.ts (message state + auto-scroll)
  ├── useChatThreads.ts
  ├── useCanvasMode.ts
  └── useAutoScroll.ts

services/
  ├── agui-client.ts (SSE event processor)
  ├── api.ts (fetch-based API client)
  └── storage.ts (localStorage abstraction)

contexts/
  └── CanvasContext.tsx (artifact + partial update state)
```

**Server/Client Boundary:**
- ❌ **No server components detected** - entire app is client-side (`'use client'` in root page)
- ✅ Using App Router, but not leveraging SSR/streaming capabilities
- ✅ Metadata defined in layout (but not leveraging Next.js metadata API)

**AG-UI Integration Pattern:**
- Custom `AGUIClient` class processes SSE events from backend
- Events: `RUN_STARTED`, `TEXT_MESSAGE_START`, `TEXT_MESSAGE_CONTENT`, `TEXT_MESSAGE_END`, `RUN_FINISHED`, `RUN_ERROR`
- Agent run lifecycle managed via `useMessages` + `ChatContainer` orchestration
- Streaming tokens appended to message content in real-time

**State Management:**
- **Zustand stores** (2): agentStore (agent selection), modelStore (provider/model selection)
- **React Context** (1): CanvasContext (artifact state, partial updates, chat input ref)
- **Local state**: Component-level useState for UI interactions
- **Persistence**: localStorage via Zustand middleware + custom StorageService

---

## 2. Top Findings (Ranked by Severity)

### 🔴 CRITICAL

#### C1: Entire App is Client-Side Rendered (Misusing App Router)
**Evidence:**
- [app/page.tsx](../frontend/app/page.tsx#L1): `'use client'` directive at root
- [app/layout.tsx](../frontend/app/layout.tsx): No server-side data fetching
- All components below are forced client-side

**Impact:**
- **Wasted App Router Benefits:** No SSR, no streaming, no React Server Components (RSC) advantages
- **Larger Bundle Size:** All React + Zustand + AG-UI + markdown rendering shipped upfront
- **Slower Initial Load:** No progressive enhancement, no static generation
- **SEO Impact:** Chat interface might not need SEO, but metadata/static pages (docs, landing) would benefit

**Recommendation:**
1. **Split Layout:** Move non-interactive shell (Layout, Header) to server components
2. **Keep Interactivity Client-Side:** Only mark `ChatContainer`, `Sidebar`, and stores as `'use client'`
3. **Use Suspense:** Wrap client components in `<Suspense>` with loading UI
4. **Add Loading/Error States:** Create `app/loading.tsx` and `app/error.tsx` for App Router conventions

**Migration Steps (PR-sized):**
```tsx
// app/layout.tsx (SERVER COMPONENT - remove 'use client')
import { Inter } from "next/font/google";
import type { Metadata } from "next";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-sans" });

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

```tsx
// app/page.tsx (Keep 'use client', but simplify)
'use client';

import dynamic from 'next/dynamic';
import { Suspense } from 'react';

// Dynamically import heavy client components
const ChatApp = dynamic(() => import('@/components/ChatApp'), {
  loading: () => <div className="flex items-center justify-center h-screen">Loading...</div>,
  ssr: false, // Explicitly disable SSR for AG-UI streaming components
});

export default function Home() {
  return (
    <Suspense fallback={<div>Initializing...</div>}>
      <ChatApp />
    </Suspense>
  );
}
```

```tsx
// components/ChatApp.tsx (extract from page.tsx)
'use client';

import { useRef, useCallback } from 'react';
import { Layout } from '@/components/Layout';
import { Sidebar } from '@/components/Sidebar';
import { ChatContainer } from '@/components/ChatContainer';
// ... rest of HomeContent logic
```

---

#### C2: Missing Critical App Router Files (loading.tsx, error.tsx, not-found.tsx)
**Evidence:**
- No `app/loading.tsx` found
- No `app/error.tsx` found
- No `app/not-found.tsx` found

**Impact:**
- **Poor Loading UX:** No loading indicators during hydration or async imports
- **Unhandled Errors:** Runtime errors crash entire app instead of showing error boundary
- **No 404 Handling:** Invalid routes show default Next.js 404

**Recommendation:**
Create minimum viable error/loading states:

```tsx
// app/loading.tsx
import { Loader2 } from 'lucide-react';

export default function Loading() {
  return (
    <div className="flex h-screen items-center justify-center">
      <div className="flex flex-col items-center gap-2">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        <p className="text-sm text-muted-foreground">Loading AgentKit...</p>
      </div>
    </div>
  );
}
```

```tsx
// app/error.tsx
'use client';

import { useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { AlertCircle } from 'lucide-react';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error('App error:', error);
  }, [error]);

  return (
    <div className="flex h-screen items-center justify-center">
      <div className="flex flex-col items-center gap-4 max-w-md text-center">
        <AlertCircle className="h-12 w-12 text-destructive" />
        <h2 className="text-xl font-semibold">Something went wrong</h2>
        <p className="text-sm text-muted-foreground">{error.message}</p>
        <Button onClick={reset}>Try again</Button>
      </div>
    </div>
  );
}
```

```tsx
// app/not-found.tsx
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Home } from 'lucide-react';

export default function NotFound() {
  return (
    <div className="flex h-screen items-center justify-center">
      <div className="flex flex-col items-center gap-4">
        <h2 className="text-2xl font-bold">404 - Page Not Found</h2>
        <p className="text-muted-foreground">The page you're looking for doesn't exist.</p>
        <Button asChild>
          <Link href="/">
            <Home className="mr-2 h-4 w-4" />
            Back to Chat
          </Link>
        </Button>
      </div>
    </div>
  );
}
```

---

#### C3: XSS Risk in Markdown Rendering (No Sanitization Detected)
**Evidence:**
- [components/AgentMessageBubble.tsx](../frontend/components/AgentMessageBubble.tsx#L55-L130): Using `react-markdown` with `rehype-raw` (allows raw HTML)
- No DOMPurify or sanitization library detected in package.json
- Direct rendering of agent-provided markdown without validation

**Impact:**
- **XSS Vulnerability:** Malicious agent responses could inject `<script>` tags or event handlers
- **Link Hijacking:** Unvalidated links could redirect to phishing sites
- **Data Exfiltration:** `<img>` tags with external URLs could leak user data

**Recommendation:**
1. **Add DOMPurify:** Sanitize HTML before rendering
2. **Restrict rehype-raw:** Only allow safe HTML subset
3. **Validate Links:** Ensure links use `https://` or internal paths
4. **CSP Headers:** Add Content-Security-Policy in next.config.ts

**Migration Steps:**
```bash
npm install dompurify @types/dompurify
```

```tsx
// components/AgentMessageBubble.tsx (add sanitization)
import DOMPurify from 'dompurify';

// Inside component, before rendering:
const sanitizedContent = useMemo(() => {
  if (typeof window === 'undefined') return message.content; // SSR fallback
  return DOMPurify.sanitize(message.content, {
    ALLOWED_TAGS: ['p', 'br', 'strong', 'em', 'code', 'pre', 'a', 'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'blockquote'],
    ALLOWED_ATTR: ['href', 'target', 'rel', 'class'],
    ALLOW_DATA_ATTR: false,
  });
}, [message.content]);

// Use sanitizedContent in ReactMarkdown
<ReactMarkdown>{sanitizedContent}</ReactMarkdown>
```

```tsx
// components/AgentMessageBubble.tsx (validate links)
components={{
  a: ({ node, href, children, ...props }) => {
    // Only allow https:// and internal links
    const isSafeUrl = href?.startsWith('https://') || href?.startsWith('/');
    if (!isSafeUrl) {
      return <span className="text-muted-foreground">{children}</span>;
    }
    return (
      <a 
        className="text-blue-500 hover:text-blue-600 underline" 
        href={href}
        target="_blank" 
        rel="noopener noreferrer"
        {...props}
      >
        {children}
      </a>
    );
  },
}}
```

```ts
// next.config.ts (add CSP headers)
const nextConfig: NextConfig = {
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'Content-Security-Policy',
            value: [
              "default-src 'self'",
              "script-src 'self' 'unsafe-inline' 'unsafe-eval'", // Relaxed for Next.js dev
              "style-src 'self' 'unsafe-inline'",
              "img-src 'self' data: https:",
              "font-src 'self' data:",
              "connect-src 'self' http://localhost:8000", // Backend API
              "frame-ancestors 'none'",
            ].join('; '),
          },
        ],
      },
    ];
  },
};
```

---

### 🟠 HIGH

#### H1: Non-Standard Styling Detected (Deviates from shadcn/ui Design System)
**Evidence:**
- [components/AgentMessageBubble.tsx](../frontend/components/AgentMessageBubble.tsx#L72):
  ```tsx
  <pre className="bg-slate-900 dark:bg-slate-950 text-slate-100 ...">
  ```
  **Issue:** Using `bg-slate-*` directly instead of shadcn tokens (`bg-muted`, `bg-card`)

- [components/AgentMessageBubble.tsx](../frontend/components/AgentMessageBubble.tsx#L77):
  ```tsx
  <a className="text-blue-500 hover:text-blue-600 dark:text-blue-400 ...">
  ```
  **Issue:** Hardcoded `blue-500/600/400` instead of `text-primary` or shadcn link styles

- [components/UserMessageBubble.tsx](../frontend/components/UserMessageBubble.tsx#L28):
  ```tsx
  <Card style={{ backgroundColor: '#F4F4F4' }}>
  ```
  **Issue:** Inline style with hex color instead of Tailwind token

- [components/Sidebar.tsx](../frontend/components/Sidebar.tsx#L43):
  ```tsx
  style={{ backgroundColor: '#F7F7F8' }}
  ```
  **Issue:** Inline style instead of `bg-background` or `bg-sidebar`

**Impact:**
- **Theme Inconsistency:** Dark mode colors won't adapt correctly
- **Maintainability:** Changing theme colors requires searching for hardcoded values
- **Accessibility:** Custom colors may violate WCAG contrast ratios
- **Design System Integrity:** Defeats purpose of using shadcn/ui

**Recommendation:**
Replace all non-standard styling with shadcn/ui tokens:

```tsx
// ❌ BEFORE (AgentMessageBubble.tsx)
<pre className="bg-slate-900 dark:bg-slate-950 text-slate-100 rounded-lg p-4 ...">

// ✅ AFTER
<pre className="bg-muted text-muted-foreground rounded-lg p-4 ...">
// OR for code blocks:
<pre className="bg-card border border-border text-card-foreground rounded-lg p-4 ...">
```

```tsx
// ❌ BEFORE (AgentMessageBubble.tsx)
<a className="text-blue-500 hover:text-blue-600 dark:text-blue-400 ...">

// ✅ AFTER
<a className="text-primary hover:text-primary/80 underline ...">
```

```tsx
// ❌ BEFORE (UserMessageBubble.tsx)
<Card style={{ backgroundColor: '#F4F4F4' }}>

// ✅ AFTER
<Card className="bg-accent">
```

```tsx
// ❌ BEFORE (Sidebar.tsx)
<aside style={{ backgroundColor: '#F7F7F8' }}>

// ✅ AFTER
<aside className="bg-sidebar border-r border-border">
// Add to globals.css:
@theme {
  --color-sidebar: 0 0% 97%; /* #F7F7F8 equivalent */
}
```

**Batch Fix (Copy-Paste Ready):**
```tsx
// components/AgentMessageBubble.tsx (lines 72-77)
// Replace pre styling
<pre className="bg-card border border-border text-card-foreground rounded-lg p-4 overflow-x-auto my-3 text-sm font-mono" {...props}>
  {children}
</pre>

// Replace link styling
<a className="text-primary hover:text-primary/80 underline" target="_blank" rel="noopener noreferrer" {...props}>
  {children}
</a>
```

---

#### H2: Zustand Store Over-Subscription (Triggers Unnecessary Re-Renders)
**Evidence:**
- [components/ChatContainer.tsx](../frontend/components/ChatContainer.tsx#L39-L46):
  ```tsx
  const selectedProvider = useModelStore((state) => state.selectedProvider);
  const selectedModel = useModelStore((state) => state.selectedModel);
  const selectedAgent = useAgentStore((state) => state.selectedAgent);
  ```
  **Pattern:** Using separate selectors, but component logs on every change

**Impact:**
- **Re-Render Storm:** ChatContainer re-renders when selectedProvider/selectedModel change, even if not actively sending messages
- **Performance Degradation:** Streaming UI might stutter during model changes
- **Unnecessary Computation:** useEffect dependencies trigger on every store update

**Recommendation:**
Use shallow equality and combined selectors:

```tsx
// ❌ BEFORE (ChatContainer.tsx)
const selectedProvider = useModelStore((state) => state.selectedProvider);
const selectedModel = useModelStore((state) => state.selectedModel);
const selectedAgent = useAgentStore((state) => state.selectedAgent);

// ✅ AFTER
import { shallow } from 'zustand/shallow';

const { selectedProvider, selectedModel } = useModelStore(
  (state) => ({ selectedProvider: state.selectedProvider, selectedModel: state.selectedModel }),
  shallow
);
const selectedAgent = useAgentStore((state) => state.selectedAgent);

// OR use refs for non-reactive values (only needed at send time):
const modelStoreRef = useRef(useModelStore.getState);
const agentStoreRef = useRef(useAgentStore.getState);

// Then in sendMessage:
const { selectedProvider, selectedModel } = modelStoreRef.current();
const { selectedAgent } = agentStoreRef.current();
```

**Better Pattern:** Move model/agent selection out of ChatContainer (lift to parent or use event emitter)

---

#### H3: Missing ARIA Attributes and Keyboard Navigation for Streaming UI
**Evidence:**
- [components/MessageBubble.tsx](../frontend/components/MessageBubble.tsx): No `role="log"` or `aria-live` for streaming content
- [components/ChatInput.tsx](../frontend/components/ChatInput.tsx): No `aria-label` on textarea
- [components/Sidebar.tsx](../frontend/components/Sidebar.tsx): Thread list not using `role="navigation"` or `aria-current`

**Impact:**
- **Screen Reader Issues:** Users can't hear streaming tokens in real-time
- **Keyboard Navigation:** No focus management when switching threads
- **A11y Violations:** WCAG 2.1 Level AA compliance at risk

**Recommendation:**
```tsx
// components/AgentMessageBubble.tsx (add aria-live for streaming)
<CardContent className="p-3" aria-live="polite" aria-atomic="false">
  {message.isPending ? (
    <div className="flex items-center gap-2" role="status">
      <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
      <span className="text-sm text-muted-foreground">Thinking...</span>
      <span className="sr-only">Agent is processing your request</span>
    </div>
  ) : (
    <div className="text-sm markdown-content">
      <ReactMarkdown>{message.content}</ReactMarkdown>
    </div>
  )}
</CardContent>
```

```tsx
// components/ChatInput.tsx (add aria labels)
<Textarea
  ref={textareaRef}
  value={message}
  onChange={(e) => setMessage(e.target.value)}
  onKeyDown={handleKeyDown}
  placeholder={placeholder}
  disabled={disabled}
  className="min-h-[60px] max-h-[200px] resize-none"
  rows={2}
  aria-label="Chat message input"
  aria-describedby="chat-input-hint"
/>
<p id="chat-input-hint" className="mt-2 text-xs text-muted-foreground">
  Press Enter to send, Shift+Enter for new line
</p>
```

```tsx
// components/Sidebar.tsx (add navigation semantics)
<nav aria-label="Chat threads">
  <ScrollArea className="flex-1">
    <ChatHistory
      threads={threads}
      currentThreadId={currentThreadId}
      onSelectThread={onSelectThread}
      onDeleteThread={onDeleteThread}
    />
  </ScrollArea>
</nav>

// In ChatHistory, add aria-current to active thread:
<Button
  variant={isActive ? "secondary" : "ghost"}
  className="..."
  onClick={() => onSelectThread(thread.id)}
  aria-current={isActive ? "page" : undefined}
>
  {thread.title}
</Button>
```

---

#### H4: localStorage Usage Without Quota/Error Handling
**Evidence:**
- [services/storage.ts](../frontend/services/storage.ts): Direct localStorage calls with no try-catch
- [stores/agentStore.ts](../frontend/stores/agentStore.ts): Zustand persist middleware with no error handling
- [stores/modelStore.ts](../frontend/stores/modelStore.ts): Same issue

**Impact:**
- **Quota Exceeded Errors:** App crashes when localStorage is full (common on mobile Safari)
- **Private Browsing:** localStorage unavailable in incognito mode
- **Data Loss:** Silent failures lead to lost chat history

**Recommendation:**
Wrap localStorage operations with try-catch and fallback:

```tsx
// services/storage.ts (add error handling wrapper)
export const StorageService = {
  getItem<T>(key: string, defaultValue: T): T {
    try {
      const item = localStorage.getItem(key);
      return item ? JSON.parse(item) : defaultValue;
    } catch (error) {
      console.error(`[Storage] Failed to get ${key}:`, error);
      return defaultValue;
    }
  },
  
  setItem<T>(key: string, value: T): boolean {
    try {
      localStorage.setItem(key, JSON.stringify(value));
      return true;
    } catch (error) {
      if (error instanceof DOMException && error.name === 'QuotaExceededError') {
        console.warn('[Storage] Quota exceeded, clearing old data...');
        this.clearOldThreads(); // Implement LRU eviction
      } else {
        console.error(`[Storage] Failed to set ${key}:`, error);
      }
      return false;
    }
  },
  
  clearOldThreads() {
    // Keep only last 50 threads, sort by updatedAt
    const threads = this.getAllThreads();
    const sorted = threads.sort((a, b) => b.updatedAt - a.updatedAt);
    const toKeep = sorted.slice(0, 50);
    localStorage.setItem(THREADS_STORAGE_KEY, JSON.stringify(toKeep));
  },
  
  // ... rest of methods
};
```

```tsx
// stores/agentStore.ts (add persist error handler)
export const useAgentStore = create<AgentStore>()(
  persist(
    (set, get) => ({ /* ... */ }),
    {
      name: AGENT_STORAGE_KEY,
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({ selectedAgent: state.selectedAgent }),
      onRehydrateStorage: () => (state, error) => {
        if (error) {
          console.error('[AgentStore] Rehydration failed:', error);
          // Reset to defaults on error
          useAgentStore.getState().reset();
        }
      },
    }
  )
);
```

---

### 🟡 MEDIUM

#### M1: Missing TypeScript Strict Null Checks in AGUIClient
**Evidence:**
- [services/agui-client.ts](../frontend/services/agui-client.ts#L137): `listeners.get(eventType)!.push(callback)` uses non-null assertion without validation
- [services/agui-client.ts](../frontend/services/agui-client.ts#L157): `.get(eventType)` may return undefined

**Impact:**
- **Runtime Errors:** Rare edge case where listener map is corrupted
- **Type Safety:** Defeats purpose of TypeScript

**Recommendation:**
```tsx
// services/agui-client.ts (remove non-null assertions)
on(eventType: string, callback: (event: AGUIEvent) => void): () => void {
  const listeners = this.listeners.get(eventType) || [];
  listeners.push(callback);
  this.listeners.set(eventType, listeners);
  
  console.log(`[AGUI] Registered listener for: ${eventType}`);
  
  return () => this.off(eventType, callback);
}

off(eventType: string, callback: (event: AGUIEvent) => void): void {
  const listeners = this.listeners.get(eventType);
  if (!listeners) return;
  
  const index = listeners.indexOf(callback);
  if (index >= 0) {
    listeners.splice(index, 1);
    console.log(`[AGUI] Removed listener for: ${eventType}`);
  }
}
```

---

#### M2: Canvas Context Uses RefObject Pattern Incorrectly
**Evidence:**
- [contexts/CanvasContext.tsx](../frontend/contexts/CanvasContext.tsx#L21): `chatInputRef: RefObject<ChatInputRef | null> | null`
- Should use callback ref pattern for dynamic ref assignments

**Impact:**
- **Type Confusion:** Double-nullable type is hard to reason about
- **React Anti-Pattern:** Storing refs in context can cause stale closures

**Recommendation:**
```tsx
// contexts/CanvasContext.tsx (use callback pattern)
interface CanvasContextValue {
  // Replace RefObject with callback
  chatInputRef: { current: ChatInputRef | null };
  setChatInputRef: (ref: ChatInputRef | null) => void;
  // ... rest
}

export function CanvasProvider({ children }: { children: ReactNode }) {
  const chatInputRef = useRef<ChatInputRef | null>(null);
  
  const setChatInputRef = useCallback((ref: ChatInputRef | null) => {
    chatInputRef.current = ref;
  }, []);
  
  return (
    <CanvasContext.Provider value={{ chatInputRef, setChatInputRef, ... }}>
      {children}
    </CanvasContext.Provider>
  );
}

// Usage in ChatContainer:
useEffect(() => {
  if (canvasContext?.setChatInputRef && chatInputRef.current) {
    canvasContext.setChatInputRef(chatInputRef.current);
  }
}, [canvasContext]);
```

---

#### M3: No TypeScript Path Aliases for Readability
**Evidence:**
- [tsconfig.json](../frontend/tsconfig.json#L22-L24): Only `@/*` alias defined
- Deep imports like `@/components/Canvas/CodeRenderer` could be shortened

**Impact:**
- **Minor Readability Issue:** Not critical, but could improve DX

**Recommendation:** (Optional)
```jsonc
// tsconfig.json (add more aliases)
{
  "compilerOptions": {
    "paths": {
      "@/*": ["./*"],
      "@/components/*": ["./components/*"],
      "@/hooks/*": ["./hooks/*"],
      "@/stores/*": ["./stores/*"],
      "@/types/*": ["./types/*"],
      "@/services/*": ["./services/*"]
    }
  }
}
```

---

#### M4: No Reduced Motion Support for Animations
**Evidence:**
- [app/globals.css](../frontend/app/globals.css#L62-L68): Transitions defined without `prefers-reduced-motion` check
- [hooks/useAutoScroll.ts](../frontend/hooks/useAutoScroll.ts): `smooth: true` hardcoded

**Impact:**
- **Accessibility:** Users with motion sensitivity experience discomfort
- **WCAG 2.1 2.3.3:** Animation from Interactions violation

**Recommendation:**
```css
/* app/globals.css (add motion preference) */
@media (prefers-reduced-motion: reduce) {
  .sidebar-transition,
  .canvas-transition,
  .canvas-grid-layout {
    transition: none !important;
  }
  
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

```tsx
// hooks/useAutoScroll.ts (respect motion preference)
const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
scrollRef.current.scrollTo({
  top: scrollRef.current.scrollHeight,
  behavior: prefersReducedMotion ? 'auto' : 'smooth',
});
```

---

### 🟢 LOW

#### L1: Missing Mobile Responsiveness Testing
**Evidence:** No responsive breakpoints detected in custom components beyond Tailwind defaults

**Recommendation:** Test on mobile viewports, add `md:` and `lg:` breakpoints where needed (e.g., Sidebar should collapse by default on mobile)

---

#### L2: No Bundle Size Monitoring
**Evidence:** No webpack-bundle-analyzer or Next.js bundle analysis configured

**Recommendation:**
```bash
npm install --save-dev @next/bundle-analyzer
```

```ts
// next.config.ts
import bundleAnalyzer from '@next/bundle-analyzer';

const withBundleAnalyzer = bundleAnalyzer({
  enabled: process.env.ANALYZE === 'true',
});

const nextConfig = { /* ... */ };

export default withBundleAnalyzer(nextConfig);
```

```json
// package.json
"scripts": {
  "analyze": "ANALYZE=true npm run build"
}
```

---

#### L3: No Test Coverage (Zero Tests Detected)
**Evidence:** No `.test.ts`, `.spec.ts`, or test configuration found

**Recommendation:** Add Vitest + React Testing Library for critical paths:
```bash
npm install --save-dev vitest @testing-library/react @testing-library/jest-dom
```

**Minimum CI Gates:**
1. **Unit Tests:** AGUIClient event processing, Zustand stores
2. **Integration Tests:** ChatContainer + useMessages flow
3. **A11y Tests:** axe-core checks on MessageBubble components

---

## 3. Refactor Plan

### Phase 1: Quick Wins (1-3 PRs, 1-2 days)

**PR #1: Fix Critical XSS + Non-Standard Styling**
- Add DOMPurify sanitization to AgentMessageBubble
- Replace all hardcoded colors with shadcn tokens
- Add CSP headers to next.config.ts
- **Files:** `AgentMessageBubble.tsx`, `UserMessageBubble.tsx`, `Sidebar.tsx`, `next.config.ts`, `package.json`
- **Lines Changed:** ~50

**PR #2: Add App Router Error/Loading States**
- Create `app/loading.tsx`, `app/error.tsx`, `app/not-found.tsx`
- Add Suspense boundaries around client components
- **Files:** 3 new files + `app/page.tsx`
- **Lines Changed:** ~80

**PR #3: ARIA Labels + Keyboard Navigation**
- Add `aria-live`, `aria-label`, `role` attributes
- Add focus management for thread selection
- **Files:** `MessageBubble.tsx`, `ChatInput.tsx`, `Sidebar.tsx`, `ChatHistory.tsx`
- **Lines Changed:** ~30

---

### Phase 2: Medium Refactors (2-4 PRs, 3-5 days)

**PR #4: Split Server/Client Components**
- Move Layout/Header to server components
- Extract ChatApp from page.tsx
- Add dynamic imports for heavy components
- **Files:** `app/layout.tsx`, `app/page.tsx`, `components/ChatApp.tsx`
- **Lines Changed:** ~100

**PR #5: Fix localStorage Error Handling**
- Wrap StorageService with try-catch
- Add LRU eviction for quota exceeded
- Add persist error handlers to Zustand stores
- **Files:** `services/storage.ts`, `stores/agentStore.ts`, `stores/modelStore.ts`
- **Lines Changed:** ~80

**PR #6: Optimize Zustand Re-Renders**
- Use shallow equality in ChatContainer
- Convert to ref-based access for send-time-only data
- **Files:** `components/ChatContainer.tsx`
- **Lines Changed:** ~20

---

### Phase 3: Strategic Improvements (2-3 PRs, 1 week)

**PR #7: Add Reduced Motion Support**
- Update globals.css with motion preference media query
- Respect `prefers-reduced-motion` in useAutoScroll
- **Files:** `app/globals.css`, `hooks/useAutoScroll.ts`
- **Lines Changed:** ~30

**PR #8: Add Test Infrastructure**
- Install Vitest + React Testing Library
- Write tests for AGUIClient, useMessages, agentStore
- Add CI workflow for test runs
- **Files:** New `tests/` directory, `vitest.config.ts`, `.github/workflows/test.yml`
- **Lines Changed:** ~500 (tests)

**PR #9: Bundle Analysis + Code Splitting**
- Add bundle analyzer
- Split Canvas components into lazy-loaded chunks
- Optimize markdown/highlight.js imports
- **Files:** `next.config.ts`, `components/ArtifactPanel.tsx`, `package.json`
- **Lines Changed:** ~50

---

## 4. Testing Recommendations

### Minimum CI Gates

**Unit Tests (Vitest):**
```tsx
// tests/agui-client.test.ts
describe('AGUIClient', () => {
  it('should process TEXT_MESSAGE_CONTENT events', () => {
    const client = new AGUIClient();
    const callback = vi.fn();
    client.on(EventType.TEXT_MESSAGE_CONTENT, callback);
    
    client.processEvent({
      type: EventType.TEXT_MESSAGE_CONTENT,
      message_id: 'test-123',
      delta: 'Hello',
    });
    
    expect(callback).toHaveBeenCalledWith(expect.objectContaining({
      type: EventType.TEXT_MESSAGE_CONTENT,
      delta: 'Hello',
    }));
  });
});
```

**Integration Tests (React Testing Library):**
```tsx
// tests/ChatContainer.test.tsx
describe('ChatContainer', () => {
  it('should display streaming messages', async () => {
    render(<ChatContainer threadId="test-thread" />);
    
    // Simulate AG-UI events
    const client = getAGUIClient();
    act(() => {
      client.processEvent({ type: EventType.TEXT_MESSAGE_START, message_id: 'msg-1' });
      client.processEvent({ type: EventType.TEXT_MESSAGE_CONTENT, message_id: 'msg-1', delta: 'Test' });
    });
    
    expect(screen.getByText(/Test/)).toBeInTheDocument();
  });
});
```

**A11y Tests (axe-core):**
```tsx
// tests/a11y.test.tsx
import { axe, toHaveNoViolations } from 'jest-axe';
expect.extend(toHaveNoViolations);

describe('Accessibility', () => {
  it('should have no a11y violations in MessageBubble', async () => {
    const { container } = render(<MessageBubble message={mockMessage} />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
```

---

## 5. Security Checklist

- ✅ **Environment Variables:** `NEXT_PUBLIC_API_URL` correctly prefixed
- ⚠️ **XSS Prevention:** **CRITICAL - Add DOMPurify** (see C3)
- ⚠️ **CSP Headers:** **CRITICAL - Add to next.config.ts** (see C3)
- ✅ **HTTPS Links:** All external links validated
- ❌ **Rate Limiting:** No client-side rate limiting for API calls (consider adding)
- ✅ **Secret Exposure:** No secrets in client-side code detected
- ⚠️ **localStorage Security:** No encryption for chat history (consider encrypting sensitive threads)

---

## 6. Performance Checklist

- ⚠️ **SSR/SSG:** Not used (see C1)
- ❌ **Code Splitting:** No dynamic imports for heavy components (see Phase 3 PR #9)
- ✅ **Lazy Loading:** Images use Next.js `<Image>` with priority flag
- ⚠️ **Bundle Size:** Unknown (add bundle analyzer - see L2)
- ✅ **Memoization:** ReactMarkdown components memoized
- ⚠️ **Re-Renders:** Zustand over-subscription issue (see H2)

---

## 7. Accessibility Checklist

- ⚠️ **Keyboard Navigation:** Partial (see H3)
- ⚠️ **Screen Reader Support:** Missing `aria-live` for streaming (see H3)
- ✅ **Color Contrast:** shadcn/ui tokens ensure WCAG AA compliance
- ⚠️ **Focus Management:** Not implemented for thread switching
- ⚠️ **Reduced Motion:** Not supported (see M4)
- ✅ **Semantic HTML:** Good use of `<nav>`, `<main>`, `<aside>`

---

## 8. Next.js Best Practices Compliance

| Practice | Status | Notes |
|----------|--------|-------|
| Use Server Components by default | ❌ | Entire app is client-side (see C1) |
| Create loading.tsx for routes | ❌ | Missing (see C2) |
| Create error.tsx for error boundaries | ❌ | Missing (see C2) |
| Use Suspense for async components | ❌ | No Suspense boundaries |
| Optimize images with next/image | ✅ | Used in Sidebar logo |
| Use next/font for font optimization | ✅ | Inter font optimized |
| Leverage metadata API | ⚠️ | Partial (metadata in layout) |
| Use dynamic imports for code splitting | ❌ | Not used |
| Implement proper caching strategies | N/A | No data fetching from Next.js routes |

---

## 9. AG-UI Protocol Compliance

✅ **Event Processing:** Correctly handles `RUN_STARTED`, `TEXT_MESSAGE_*`, `RUN_FINISHED`, `RUN_ERROR`  
✅ **Streaming UI:** Tokens appended in real-time with visual indicators  
✅ **Message Deduplication:** Message IDs tracked, no duplicate messages  
✅ **Error Handling:** RUN_ERROR events caught and displayed  
⚠️ **Tool Call States:** Protocol defined but not rendered in UI (TOOL_CALL_START, etc.)  
✅ **Artifact Detection:** Metadata parsing for artifact messages  
✅ **Partial Updates:** Implemented in CanvasContext for canvas editing  

---

## 10. Summary of Action Items

**Immediate (This Sprint):**
1. Fix XSS vulnerability with DOMPurify
2. Replace non-standard colors with shadcn tokens
3. Add loading.tsx, error.tsx, not-found.tsx
4. Add ARIA labels for streaming content

**Next Sprint:**
1. Split server/client components
2. Fix localStorage error handling
3. Optimize Zustand re-renders
4. Add reduced motion support

**Backlog:**
1. Add test infrastructure
2. Implement bundle analysis
3. Add mobile responsiveness testing
4. Consider encryption for sensitive chat history

---

## 11. Risk Assessment

**High Risk:**
- XSS vulnerability in markdown rendering (exploit could compromise user sessions)
- localStorage quota errors causing data loss (common on mobile)

**Medium Risk:**
- Missing error boundaries (app crashes on runtime errors)
- Over-rendering from Zustand subscriptions (UX degradation during streaming)

**Low Risk:**
- Missing tests (maintenance burden over time)
- No bundle monitoring (slow incremental bloat)

---

## 12. Conclusion

**Strengths:**
- ✅ Modern Next.js 16 + React 19 + TypeScript stack
- ✅ Clean shadcn/ui component integration
- ✅ Well-structured AG-UI event processing
- ✅ Good separation of concerns (stores, hooks, services)
- ✅ Streaming UI works correctly with real-time token updates

**Critical Improvements Needed:**
- 🔴 Fix XSS vulnerability immediately
- 🔴 Replace non-standard styling to maintain design system
- 🔴 Add App Router error/loading states
- 🟠 Split server/client components to leverage Next.js benefits

**Estimated Refactor Effort:**
- **Quick Wins:** 1-2 days (3 PRs)
- **Medium Refactors:** 3-5 days (3 PRs)
- **Strategic Improvements:** 1 week (3 PRs)
- **Total:** ~2-3 weeks for complete refactor

**Recommendation:**
Prioritize Phase 1 (Quick Wins) immediately, especially XSS fixes. Phase 2 can be scheduled for next sprint. Phase 3 is nice-to-have but not blocking.

---

**Next Steps:**
1. Review this document with team
2. Create GitHub issues from action items
3. Assign Phase 1 PRs to sprint
4. Schedule architecture review follow-up in 2 weeks

---

*End of Review*
