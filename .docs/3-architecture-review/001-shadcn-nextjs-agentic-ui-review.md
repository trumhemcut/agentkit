# Frontend Architecture Review: shadcn/ui Implementation & Next.js Patterns

**Review Date:** December 26, 2025  
**Reviewer:** Frontend Principal Engineer (Agentic AI Specialization)  
**Scope:** AgentKit Frontend (Next.js 16.1.1 + shadcn/ui + AG-UI)

---

## 1. Architecture Summary

### Inferred Structure
- **Framework:** Next.js 16.1.1 with App Router
- **UI Library:** shadcn/ui (New York style, neutral base color)
- **State Management:** Zustand with persist middleware
- **Agent Protocol:** Custom AG-UI client over SSE
- **Styling:** Tailwind CSS v4 with CSS variables for theming
- **TypeScript:** Full coverage with path aliases (`@/*`)

### Component Architecture
```
app/
  ├── layout.tsx          ❌ CRITICAL: Server component but no metadata optimization
  └── page.tsx            ✅ "use client" - correct for interactive UI

components/
  ├── ui/                 ✅ shadcn/ui components (proper CVA usage)
  ├── *MessageBubble.tsx  ⚠️ Non-standard styling detected
  ├── Sidebar.tsx         ❌ CRITICAL: Inline styles instead of design tokens
  └── Canvas/             ⚠️ Direct color usage instead of semantic tokens
```

### Server/Client Boundaries
- **Observation:** Nearly all components use `"use client"` including potential server-renderable components
- **Issue:** Missed SSR optimization opportunities (Header, Layout wrapper components)

---

## 2. Top Findings (Ranked by Severity)

### 🔴 CRITICAL Issues

#### **C1: Inline Style Injection Breaking Design System**
**Evidence:**
- [Sidebar.tsx](frontend/components/Sidebar.tsx#L43): `style={{ backgroundColor: '#F7F7F8' }}`
- [UserMessageBubble.tsx](frontend/components/UserMessageBubble.tsx#L28): `style={{ backgroundColor: '#F4F4F4' }}`

**Impact:**
- Breaks shadcn/ui design token system
- Hardcoded colors bypass theme switching (light/dark mode)
- CSS-in-JS anti-pattern in Tailwind CSS environment
- Not responsive to `prefers-color-scheme` changes

**Recommendation:**
Replace inline styles with semantic design tokens:

```tsx
// ❌ BEFORE - Sidebar.tsx
<aside 
  style={{ backgroundColor: '#F7F7F8' }}
  className={cn(
    "flex h-screen flex-col transition-all duration-300 ease-in-out",
    isCollapsed ? "w-16" : "w-64",
    "text-gray-900"
  )}
>

// ✅ AFTER - Use muted background token
<aside 
  className={cn(
    "flex h-screen flex-col transition-all duration-300 ease-in-out bg-muted/30",
    isCollapsed ? "w-16" : "w-64"
  )}
>
```

```tsx
// ❌ BEFORE - UserMessageBubble.tsx
<Card className="border-0" style={{ backgroundColor: '#F4F4F4' }}>

// ✅ AFTER - Use shadcn Card with muted variant
<Card className="border-0 bg-muted/50">
```

**Migration PR:**
1. Create custom CSS variable in globals.css if needed: `--sidebar-bg: var(--muted)`
2. Replace all `style={{ backgroundColor }}` with semantic Tailwind classes
3. Test light/dark mode switching

---

#### **C2: Arbitrary Color Classes Bypassing Design System**
**Evidence:**
- [AvatarIcon.tsx](frontend/components/AvatarIcon.tsx#L19): `bg-blue-500`, `bg-green-500`
- [AgentMessageBubble.tsx](frontend/components/AgentMessageBubble.tsx#L72-L77): `bg-slate-900`, `text-blue-500`, `text-blue-600`, etc.
- [CodeRenderer.tsx](frontend/components/Canvas/CodeRenderer.tsx#L39): `bg-blue-500`

**Impact:**
- Hard-coded Tailwind colors don't respect shadcn theme configuration
- Inconsistent brand colors (blue-500 vs primary token)
- Dark mode handling is duplicated per-component instead of semantic

**Recommendation:**
Map all arbitrary colors to shadcn semantic tokens:

```tsx
// ❌ BEFORE - AvatarIcon.tsx
<AvatarFallback className={cn(
  role === 'user' ? 'bg-blue-500' : 'bg-green-500',
  'text-white'
)}>

// ✅ AFTER - Use semantic tokens
<AvatarFallback className={cn(
  role === 'user' ? 'bg-primary' : 'bg-accent',
  'text-primary-foreground'
)}>
```

```tsx
// ❌ BEFORE - AgentMessageBubble.tsx (markdown links)
<a className="text-blue-500 hover:text-blue-600 dark:text-blue-400 dark:hover:text-blue-300 underline">

// ✅ AFTER - shadcn-native link styling
<a className="text-primary hover:text-primary/80 underline underline-offset-4">
```

```tsx
// ❌ BEFORE - CodeRenderer.tsx (streaming badge)
<div className="absolute top-2 right-2 z-10 bg-blue-500 text-white px-3 py-1 rounded-full">

// ✅ AFTER - Use badge component or semantic tokens
<Badge variant="default" className="absolute top-2 right-2 z-10">
  <Loader2 className="h-3 w-3 animate-spin" />
  Generating...
</Badge>
```

**New semantic tokens to add in globals.css:**
```css
@theme {
  --color-user-avatar: var(--color-primary);
  --color-agent-avatar: var(--color-accent);
  --color-code-block-bg: var(--color-card);
  --color-link: var(--color-primary);
}
```

---

#### **C3: Server/Client Boundary Violations**
**Evidence:**
- [app/layout.tsx](frontend/app/layout.tsx): Server component doesn't leverage static generation
- [app/page.tsx](frontend/app/page.tsx#L1): Uses `"use client"` unnecessarily for entire page
- No `loading.tsx`, `error.tsx`, or `not-found.tsx` in app directory

**Impact:**
- Missed performance wins from RSC (React Server Components)
- Entire page tree is client-rendered, increasing bundle size
- No streaming UI with Suspense for async components
- Poor SEO potential (all content client-side)

**Recommendation:**

1. **Split page.tsx into server/client layers:**
```tsx
// app/page.tsx (SERVER COMPONENT - no "use client")
import { Suspense } from 'react';
import { HomeClient } from './home-client';
import { LoadingSkeleton } from '@/components/loading-skeleton';

export default function HomePage() {
  return (
    <Suspense fallback={<LoadingSkeleton />}>
      <HomeClient />
    </Suspense>
  );
}

// app/home-client.tsx (CLIENT COMPONENT)
'use client';
// ... existing page logic
```

2. **Add App Router conventions:**
```tsx
// app/loading.tsx
import { Skeleton } from '@/components/ui/skeleton';

export default function Loading() {
  return <ChatLoadingSkeleton />;
}

// app/error.tsx
'use client';
import { Alert, AlertDescription } from '@/components/ui/alert';

export default function Error({ error, reset }: { error: Error; reset: () => void }) {
  return (
    <Alert variant="destructive">
      <AlertDescription>{error.message}</AlertDescription>
      <Button onClick={reset}>Try again</Button>
    </Alert>
  );
}
```

3. **Optimize layout.tsx:**
```tsx
// app/layout.tsx
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
  display: 'swap', // ✅ Add font display optimization
});

export const metadata: Metadata = {
  title: "AgentKit - Multi-Agent AI Assistant",
  description: "Agentic AI solution powered by LangGraph",
  // ✅ Add SEO metadata
  openGraph: {
    title: "AgentKit",
    description: "Multi-Agent AI Assistant",
    type: "website",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationMismatch> {/* ✅ Prevent hydration warnings */}
      <body className={inter.variable}>
        {children}
      </body>
    </html>
  );
}
```

---

### 🟠 HIGH Priority Issues

#### **H1: Missing Accessibility Attributes**
**Evidence:**
- **Zero ARIA attributes** found across all components (grep search returned no results)
- [MessageHistory.tsx](frontend/components/MessageHistory.tsx): No `aria-live` for streaming messages
- [ChatInput.tsx](frontend/components/ChatInput.tsx): Send button missing `aria-label`
- [Sidebar.tsx](frontend/components/Sidebar.tsx): Collapse button has `title` but no `aria-expanded`

**Impact:**
- Screen readers cannot announce agent responses in real-time
- Loading states are invisible to assistive tech
- Keyboard users have no context for icon-only buttons

**Recommendation:**

```tsx
// ✅ MessageHistory.tsx - Announce new messages
<div 
  className="h-full overflow-y-auto p-4 space-y-4" 
  ref={scrollRef}
  role="log"
  aria-live="polite"
  aria-relevant="additions"
>
  {messages.map((message) => (
    <MessageBubble key={message.id} message={message} />
  ))}
</div>

// ✅ ChatInput.tsx - Label icon button
<Button
  onClick={handleSend}
  disabled={disabled || !message.trim()}
  size="icon"
  aria-label="Send message"
>
  <Send className="h-4 w-4" />
  <span className="sr-only">Send message</span>
</Button>

// ✅ Sidebar.tsx - Announce collapse state
<Button
  variant="ghost"
  size="icon"
  onClick={onToggleCollapse}
  aria-expanded={!isCollapsed}
  aria-label={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
>
  <PanelLeftClose className="h-4 w-4" />
</Button>

// ✅ AgentMessageBubble.tsx - Loading indicator
{(message.isPending || message.isStreaming) && (
  <div className="flex items-center gap-2" role="status" aria-live="polite">
    <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
    <span>Thinking...</span>
  </div>
)}
```

---

#### **H2: Markdown Rendering Security Risk (XSS)**
**Evidence:**
- [AgentMessageBubble.tsx](frontend/components/AgentMessageBubble.tsx): Uses `react-markdown` with `rehype-raw` plugin
- No HTML sanitization visible in the code
- User/agent content rendered without validation

**Impact:**
- Potential XSS if agent returns malicious HTML in markdown
- No CSP headers detected in Next.js config
- Unsafe for multi-tenant environments

**Recommendation:**

1. **Add Content Security Policy:**
```typescript
// next.config.ts
const nextConfig: NextConfig = {
  headers: async () => [
    {
      source: '/(.*)',
      headers: [
        {
          key: 'Content-Security-Policy',
          value: [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'", // Next.js dev
            "style-src 'self' 'unsafe-inline'",
            "img-src 'self' data: blob:",
            "connect-src 'self' http://localhost:8000", // Backend API
          ].join('; '),
        },
      ],
    },
  ],
};
```

2. **Sanitize markdown output:**
```tsx
// Install: npm install rehype-sanitize
import rehypeSanitize from 'rehype-sanitize';

<ReactMarkdown
  remarkPlugins={[remarkGfm]}
  rehypePlugins={[
    rehypeHighlight,
    [rehypeSanitize, {
      // Allow safe HTML tags only
      tagNames: ['p', 'a', 'code', 'pre', 'strong', 'em', 'ul', 'ol', 'li', 'h1', 'h2', 'h3'],
      attributes: {
        a: ['href', 'title'],
        code: ['className'],
      },
    }],
  ]}
>
  {message.content}
</ReactMarkdown>
```

3. **Validate external links:**
```tsx
// components/SafeLink.tsx
export function SafeLink({ href, children, ...props }: { href: string; children: React.ReactNode }) {
  const isSafe = href.startsWith('http://') || href.startsWith('https://');
  
  if (!isSafe) {
    console.warn('[Security] Blocked unsafe link:', href);
    return <span className="text-muted-foreground">{children}</span>;
  }
  
  return (
    <a 
      href={href} 
      target="_blank" 
      rel="noopener noreferrer"
      className="text-primary hover:text-primary/80 underline"
      {...props}
    >
      {children}
    </a>
  );
}
```

---

#### **H3: Zustand Store Anti-Pattern (God Store)**
**Evidence:**
- [modelStore.ts](frontend/stores/modelStore.ts): Single store with 10+ state properties
- Store includes API logic (`loadModels`), mixing concerns
- No separation between UI state and server state

**Impact:**
- Every model/provider change triggers re-renders in all subscribers
- API calls embedded in store (should use React Query or SWR)
- Difficult to test in isolation

**Recommendation:**

**Split into domain stores:**
```typescript
// stores/model-selection.ts (UI STATE ONLY)
interface ModelSelectionStore {
  selectedProvider: string | null;
  selectedModel: string | null;
  setProvider: (id: string) => void;
  setModel: (id: string) => void;
}

// hooks/use-available-models.ts (SERVER STATE with SWR)
import useSWR from 'swr';

export function useAvailableModels() {
  const { data, error, isLoading } = useSWR(
    '/api/models',
    fetchAvailableModels,
    { revalidateOnFocus: false, dedupingInterval: 60000 }
  );
  
  return {
    models: data?.models ?? [],
    providers: data?.providers ?? [],
    isLoading,
    error,
  };
}
```

**Use shallow equality for selectors:**
```tsx
// ❌ BEFORE - Re-renders on any store change
const { selectedProvider, selectedModel, loading } = useModelStore();

// ✅ AFTER - Only re-render when specific values change
const selectedProvider = useModelStore((state) => state.selectedProvider);
const selectedModel = useModelStore((state) => state.selectedModel);
```

---

### 🟡 MEDIUM Priority Issues

#### **M1: Missing Keyboard Navigation**
**Evidence:**
- [Sidebar.tsx](frontend/components/Sidebar.tsx): No arrow key navigation for thread list
- [ChatHistory.tsx](frontend/components/ChatHistory.tsx): Thread items not keyboard-focusable when sidebar collapsed
- [ModelSelector.tsx](frontend/components/ModelSelector.tsx): DropdownMenu uses shadcn (✅ keyboard-accessible), but no documentation

**Recommendation:**
- Add `tabIndex={0}` to thread items with `onKeyDown` handler (Enter/Space to select)
- Document keyboard shortcuts in a help modal (Cmd+K for search, etc.)
- Add focus trap in dropdown menus during keyboard navigation

---

#### **M2: Custom CSS Overrides Fighting shadcn Defaults**
**Evidence:**
- [globals.css](frontend/app/globals.css#L60-L100): 67 lines of custom CSS overriding component styles
- Custom scrollbar styling duplicates shadcn ScrollArea component
- BlockNote-specific overrides (`!important` rules indicate fighting framework)

**Recommendation:**
```css
/* ❌ REMOVE - Custom scrollbar (use shadcn ScrollArea) */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

/* ✅ KEEP - But make it opt-in with utility class */
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: hsl(var(--color-muted-foreground) / 0.3);
  border-radius: 4px;
}
```

Use ScrollArea component instead:
```tsx
import { ScrollArea } from '@/components/ui/scroll-area';

<ScrollArea className="h-full">
  {/* content */}
</ScrollArea>
```

---

#### **M3: Inconsistent Loading States**
**Evidence:**
- [ModelSelector.tsx](frontend/components/ModelSelector.tsx#L46-L52): Custom loading UI
- [ChatContainer.tsx](frontend/components/ChatContainer.tsx): `isSending` state but no global loading indicator
- No skeleton screens for initial load

**Recommendation:**
Create unified loading components:
```tsx
// components/loading-states.tsx
import { Skeleton } from '@/components/ui/skeleton';

export function ChatLoadingSkeleton() {
  return (
    <div className="flex h-screen">
      <Skeleton className="w-64 h-full" /> {/* Sidebar */}
      <div className="flex-1 flex flex-col">
        <Skeleton className="h-16 w-full" /> {/* Header */}
        <div className="flex-1 p-4 space-y-4">
          <MessageSkeleton align="right" />
          <MessageSkeleton align="left" />
        </div>
      </div>
    </div>
  );
}
```

---

#### **M4: Missing Mobile Responsiveness**
**Evidence:**
- [Sidebar.tsx](frontend/components/Sidebar.tsx): Fixed width (`w-64`), no mobile drawer
- [Header.tsx](frontend/components/Header.tsx): `hidden sm:inline` for labels but no mobile alternative
- No touch gesture handling for canvas resizing

**Recommendation:**
```tsx
// Responsive sidebar with sheet for mobile
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet';

export function ResponsiveSidebar({ children }: { children: React.ReactNode }) {
  return (
    <>
      {/* Desktop sidebar */}
      <aside className="hidden md:flex w-64 h-screen">
        {children}
      </aside>
      
      {/* Mobile drawer */}
      <Sheet>
        <SheetTrigger asChild className="md:hidden">
          <Button variant="ghost" size="icon">
            <Menu className="h-5 w-5" />
          </Button>
        </SheetTrigger>
        <SheetContent side="left" className="w-64 p-0">
          {children}
        </SheetContent>
      </Sheet>
    </>
  );
}
```

---

### 🟢 LOW Priority / Enhancements

#### **L1: Missing Code Splitting**
- No dynamic imports for Canvas components (heavy CodeMirror dependency)
- Suggestion: `const CodeRenderer = dynamic(() => import('./Canvas/CodeRenderer'), { ssr: false });`

#### **L2: Console.log Statements in Production**
- 50+ console.log statements across components
- Should use structured logging library or remove in production build

#### **L3: No Error Boundaries**
- Missing React Error Boundaries for component failure isolation
- Suggestion: Wrap each major section (Sidebar, ChatContainer, Canvas) in ErrorBoundary

---

## 3. Non-Standard Styling Audit (MANDATORY)

### Summary of Violations

| File | Line | Violation | shadcn-Native Fix |
|------|------|-----------|-------------------|
| **Sidebar.tsx** | 43 | `style={{ backgroundColor: '#F7F7F8' }}` | `className="bg-muted/30"` |
| **UserMessageBubble.tsx** | 28 | `style={{ backgroundColor: '#F4F4F4' }}` | `className="bg-muted/50"` |
| **AvatarIcon.tsx** | 19 | `bg-blue-500`, `bg-green-500` | `bg-primary`, `bg-accent` |
| **AgentMessageBubble.tsx** | 72 | `bg-slate-900`, `text-slate-100` | `bg-card`, `text-card-foreground` |
| **AgentMessageBubble.tsx** | 77 | `text-blue-500 hover:text-blue-600` | `text-primary hover:text-primary/80` |
| **CodeRenderer.tsx** | 39 | `bg-blue-500 text-white` | `<Badge variant="default">` |
| **ChatHistory.tsx** | 54 | `hover:bg-gray-200` | `hover:bg-accent` |
| **globals.css** | 60-100 | Custom scrollbar, !important overrides | Use `<ScrollArea>` component |

### Why It Matters
1. **Theme Consistency:** Hardcoded colors break when users switch themes
2. **Maintainability:** Changing brand colors requires grep-replace instead of token update
3. **Dark Mode:** Each hardcoded color needs manual dark mode variant
4. **Accessibility:** Semantic tokens ensure sufficient contrast ratios

---

## 4. Security & Privacy

### Findings

#### **S1: No PII Redaction in Client Logs**
- [ChatContainer.tsx](frontend/components/ChatContainer.tsx): Logs full event objects with potential user data
- **Fix:** Redact sensitive fields before logging:
```typescript
const safeLog = (event: AGUIEvent) => {
  const { content, ...safe } = event;
  console.log('[AGUI]', safe, 'content:', content?.substring(0, 50) + '...');
};
```

#### **S2: localStorage Persistence Without Encryption**
- [modelStore.ts](frontend/stores/modelStore.ts): Uses `persist` with raw JSON
- **Risk:** API keys or tokens stored in cleartext if accidentally added to store
- **Fix:** Add encryption layer or use sessionStorage for sensitive data

---

## 5. Testing Recommendations

### Minimum CI Gates (Currently Missing)

1. **Unit Tests (Vitest + React Testing Library)**
```bash
npm install -D vitest @testing-library/react @testing-library/jest-dom
```

Test critical paths:
- Message rendering (user/agent bubbles)
- Model/agent selection state management
- AG-UI event processing
- Canvas artifact rendering

2. **Accessibility Tests (axe-core)**
```bash
npm install -D @axe-core/react
```

```tsx
// tests/a11y.test.tsx
import { axe, toHaveNoViolations } from 'jest-axe';

expect.extend(toHaveNoViolations);

test('Sidebar has no accessibility violations', async () => {
  const { container } = render(<Sidebar {...props} />);
  const results = await axe(container);
  expect(results).toHaveNoViolations();
});
```

3. **Visual Regression Tests (Playwright)**
Test theme switching, responsive breakpoints, and streaming UI states.

---

## 6. Refactor Plan

### Phase 1: Quick Wins (1-3 PRs, 1 week)

**PR #1: Fix Non-Standard Styling (Critical)**
- [ ] Replace all `style={{ backgroundColor }}` with semantic tokens
- [ ] Replace `bg-blue-500`, `bg-green-500` with `bg-primary`, `bg-accent`
- [ ] Remove hardcoded colors from markdown renderers
- [ ] Test light/dark mode switching

**PR #2: Add Accessibility Attributes (High)**
- [ ] Add `aria-live="polite"` to MessageHistory
- [ ] Add `aria-label` to all icon-only buttons
- [ ] Add `aria-expanded` to Sidebar collapse button
- [ ] Add `role="status"` to loading indicators

**PR #3: Security Hardening (High)**
- [ ] Install `rehype-sanitize` and configure
- [ ] Add CSP headers to next.config.ts
- [ ] Add link validation in markdown renderer
- [ ] Remove/redact PII from console.logs

---

### Phase 2: Medium Refactors (3-5 PRs, 2-3 weeks)

**PR #4: Server/Client Boundary Optimization**
- [ ] Split page.tsx into server wrapper + client content
- [ ] Add loading.tsx, error.tsx, not-found.tsx
- [ ] Extract Header as server component
- [ ] Add Suspense boundaries for async components

**PR #5: Zustand Store Refactor**
- [ ] Install SWR or TanStack Query
- [ ] Move API logic out of stores
- [ ] Split modelStore into selection + data stores
- [ ] Add shallow equality to all selectors

**PR #6: Mobile Responsiveness**
- [ ] Convert Sidebar to Sheet on mobile
- [ ] Add touch gestures for canvas resizing
- [ ] Test all breakpoints (sm, md, lg, xl)

**PR #7: Custom CSS Cleanup**
- [ ] Replace custom scrollbar with ScrollArea
- [ ] Remove BlockNote `!important` overrides
- [ ] Document any necessary custom styles

---

### Phase 3: Strategic Improvements (5+ PRs, 1 month+)

**PR #8: Testing Infrastructure**
- [ ] Set up Vitest + RTL
- [ ] Add unit tests for stores
- [ ] Add component tests for message bubbles
- [ ] Add E2E tests with Playwright

**PR #9: Code Splitting & Performance**
- [ ] Lazy load Canvas components
- [ ] Analyze bundle size with @next/bundle-analyzer
- [ ] Implement route prefetching
- [ ] Add React.memo to expensive components

**PR #10: Keyboard Navigation**
- [ ] Add arrow key support to thread list
- [ ] Add keyboard shortcuts (Cmd+K, Esc, etc.)
- [ ] Document shortcuts in help modal
- [ ] Add focus trap in modals

**PR #11: Error Boundaries & Monitoring**
- [ ] Add React Error Boundaries
- [ ] Integrate Sentry or similar
- [ ] Add structured logging
- [ ] Create error recovery UI

---

## 7. Next.js Compliance Checklist

- [ ] **App Router:** Using App Router ✅
- [ ] **RSC:** Leveraging Server Components ❌ (only layout.tsx)
- [ ] **Metadata API:** Using generateMetadata ❌ (static only)
- [ ] **Loading UI:** loading.tsx files ❌
- [ ] **Error Handling:** error.tsx files ❌
- [ ] **Font Optimization:** next/font ✅
- [ ] **Image Optimization:** next/image ⚠️ (only for logo)
- [ ] **Route Groups:** Organized routes ❌
- [ ] **Parallel Routes:** For multi-pane UI ❌
- [ ] **Intercepting Routes:** For modals ❌

---

## 8. Conclusion

### Strengths
✅ Proper shadcn/ui component usage (Button, Card, DropdownMenu)  
✅ Zustand with persist for state management  
✅ TypeScript coverage with path aliases  
✅ Structured component organization  
✅ AG-UI protocol integration for real-time streaming  

### Critical Gaps
❌ **Non-standard styling breaks design system** (inline styles, arbitrary colors)  
❌ **Zero accessibility attributes** (WCAG compliance risk)  
❌ **Security vulnerabilities** (XSS risk in markdown, no CSP)  
❌ **Server/Client boundary issues** (missed RSC optimization)  
❌ **No testing infrastructure** (CI/CD risk)  

### Recommended Priority
1. **Immediate (This Sprint):** Fix non-standard styling (C1, C2), add accessibility (H1), sanitize markdown (H2)
2. **Next Sprint:** Server/client optimization (C3), Zustand refactor (H3)
3. **Long-term:** Mobile responsiveness (M4), testing (Phase 3), performance optimization

---

## Appendix A: shadcn/ui Design Token Reference

```typescript
// Semantic tokens defined in globals.css
--color-background      // Page background
--color-foreground      // Text color
--color-card            // Card backgrounds
--color-muted           // Subdued backgrounds (sidebar, disabled states)
--color-accent          // Hover states, secondary highlights
--color-primary         // Brand color, CTAs
--color-destructive     // Error states, delete actions

// Usage in components
className="bg-muted text-muted-foreground"
className="bg-primary text-primary-foreground"
className="hover:bg-accent hover:text-accent-foreground"
```

---

## Appendix B: Copy-Paste Fixes

### Fix #1: Sidebar Background
```tsx
// File: frontend/components/Sidebar.tsx
// Line: 36-43

// Replace:
<aside 
  className={cn(
    "flex h-screen flex-col transition-all duration-300 ease-in-out",
    isCollapsed ? "w-16" : "w-64",
    "text-gray-900"
  )}
  style={{ backgroundColor: '#F7F7F8' }}
>

// With:
<aside 
  className={cn(
    "flex h-screen flex-col transition-all duration-300 ease-in-out bg-muted/30",
    isCollapsed ? "w-16" : "w-64"
  )}
>
```

### Fix #2: User Message Bubble
```tsx
// File: frontend/components/UserMessageBubble.tsx
// Line: 28

// Replace:
<Card className="border-0" style={{ backgroundColor: '#F4F4F4' }}>

// With:
<Card className="border-0 bg-muted/50">
```

### Fix #3: Avatar Colors
```tsx
// File: frontend/components/AvatarIcon.tsx
// Line: 18-20

// Replace:
<AvatarFallback className={cn(
  role === 'user' ? 'bg-blue-500' : 'bg-green-500',
  'text-white'
)}>

// With:
<AvatarFallback className={cn(
  role === 'user' ? 'bg-primary' : 'bg-accent',
  'text-primary-foreground'
)}>
```

### Fix #4: Add Accessibility to MessageHistory
```tsx
// File: frontend/components/MessageHistory.tsx
// Line: 29-35

// Replace:
<div className="h-full overflow-y-auto p-4 space-y-4" ref={scrollRef}>

// With:
<div 
  className="h-full overflow-y-auto p-4 space-y-4" 
  ref={scrollRef}
  role="log"
  aria-live="polite"
  aria-relevant="additions"
  aria-label="Chat message history"
>
```

---

**End of Review**
