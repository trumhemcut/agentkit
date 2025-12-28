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
