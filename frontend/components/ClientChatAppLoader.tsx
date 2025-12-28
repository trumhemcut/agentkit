'use client';

import { Suspense } from 'react';
import dynamic from 'next/dynamic';
import { CanvasProvider } from '@/contexts/CanvasContext';

// Dynamically import the heavy client component
// This reduces initial bundle size and enables proper Server/Client Component split
const ChatApp = dynamic(
  () => import('@/components/ChatApp').then(mod => ({ default: mod.ChatApp })),
  {
    loading: () => (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading AgentKit...</p>
        </div>
      </div>
    ),
    ssr: false, // AG-UI streaming requires client-side only
  }
);

interface ClientChatAppLoaderProps {
  threadId?: string;
}

export function ClientChatAppLoader({ threadId }: ClientChatAppLoaderProps) {
  return (
    <CanvasProvider>
      <Suspense fallback={<div>Initializing...</div>}>
        <ChatApp initialThreadId={threadId} />
      </Suspense>
    </CanvasProvider>
  );
}
