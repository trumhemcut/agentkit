'use client';

import { useRef, useCallback, useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import dynamic from 'next/dynamic';
import { Layout } from '@/components/Layout';
import { Sidebar } from '@/components/Sidebar';
import { ChatContainer, ChatContainerRef } from '@/components/ChatContainer';
import { useChatThreads } from '@/hooks/useChatThreads';
import { useSidebar } from '@/hooks/useSidebar';
import { useCanvasMode } from '@/hooks/useCanvasMode';
import { Message } from '@/types/chat';
import { useCanvas } from '@/contexts/CanvasContext';

// Dynamically import heavy components (BlockNote + CodeMirror)
const ArtifactPanel = dynamic(
  () => import('@/components/ArtifactPanel').then(mod => ({ default: mod.ArtifactPanel })),
  {
    loading: () => (
      <div className="flex items-center justify-center h-full bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading Canvas...</p>
        </div>
      </div>
    ),
    ssr: false,
  }
);

const ResizableDivider = dynamic(
  () => import('@/components/ResizableDivider').then(mod => ({ default: mod.ResizableDivider })),
  { ssr: false }
);

interface ChatAppProps {
  initialThreadId?: string;
}

export function ChatApp({ initialThreadId }: ChatAppProps) {
  const router = useRouter();
  const {
    threads,
    currentThread,
    currentThreadId,
    createThread,
    deleteThread,
    selectThread,
    updateThreadTitle,
    refreshThreads,
  } = useChatThreads(initialThreadId);

  const { isCollapsed, toggleCollapse, setCollapsed } = useSidebar();
  const { 
    isActive: canvasModeActive, 
    currentArtifactMessage,
    activateCanvas,
    deactivateCanvas,
    updateCurrentArtifact,
  } = useCanvasMode();
  
  const chatContainerRef = useRef<ChatContainerRef>(null);
  
  // Resizable panel widths (in percentages)
  const [chatPanelWidth, setChatPanelWidth] = useState(33.33);
  
  // Get canvas context to load and set artifactId
  const { setArtifactId, loadArtifactById } = useCanvas();
  
  // Performance tracking
  useEffect(() => {
    if (typeof window !== 'undefined' && 'performance' in window) {
      const perfData = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      if (perfData) {
        console.log('[Performance] Metrics:', {
          domContentLoaded: Math.round(perfData.domContentLoadedEventEnd - perfData.domContentLoadedEventStart),
          loadComplete: Math.round(perfData.loadEventEnd - perfData.loadEventStart),
          timeToInteractive: Math.round(perfData.domInteractive - perfData.fetchStart),
        });
      }
    }
  }, []);
  
  // Handle artifact detection from messages
  const handleArtifactDetected = useCallback((message: Message) => {
    console.log('[Home] Artifact detected, activating canvas mode:', message);
    activateCanvas(message);
    
    // Load artifact from storage and set artifactId in canvas context if present
    if (message.artifactId && message.threadId) {
      console.log('[Home] Loading artifact from storage:', message.artifactId);
      const loaded = loadArtifactById(message.artifactId, message.threadId);
      if (loaded) {
        console.log('[Home] Artifact loaded successfully from storage');
      } else {
        console.warn('[Home] Failed to load artifact from storage, setting artifactId directly');
        setArtifactId(message.artifactId);
      }
    }
    setCollapsed(true); // Auto-collapse sidebar when canvas mode activates
  }, [activateCanvas, setArtifactId, loadArtifactById, setCollapsed]);
  
  const handleNewChat = () => {
    // Create a new thread if there's no current thread or if the current thread has messages
    const hasNoThread = !currentThread;
    const hasMessages = currentThread && currentThread.messages.length > 0;
    
    if (hasNoThread || hasMessages) {
      const newThread = createThread();
      // Navigate to new thread URL
      router.push(`/thread/${newThread.id}`);
      // Deactivate canvas mode when starting a new chat
      deactivateCanvas();
    }
    
    // Focus on input after a short delay to ensure the component is rendered
    setTimeout(() => {
      chatContainerRef.current?.focusInput();
    }, 100);
  };

  const handleSelectThread = useCallback((threadId: string) => {
    selectThread(threadId);
    // Navigate to thread URL
    router.push(`/thread/${threadId}`);
  }, [selectThread, router]);
  
  const handleCloseCanvas = () => {
    deactivateCanvas();
    setCollapsed(false); // Restore sidebar when canvas closes
  };
  
  const handleResize = useCallback((leftWidth: number) => {
    setChatPanelWidth(leftWidth);
  }, []);

  return (
    <Layout
      sidebar={
        <Sidebar
          threads={threads}
          currentThreadId={currentThreadId}
          isCollapsed={isCollapsed}
          onToggleCollapse={toggleCollapse}
          onNewChat={handleNewChat}
          onSelectThread={handleSelectThread}
          onDeleteThread={deleteThread}
        />
      }
    >
      <div className={canvasModeActive ? "flex h-full canvas-grid-layout" : "flex h-full canvas-transition"}>
        <div 
          className={canvasModeActive ? "h-full overflow-hidden canvas-transition" : "flex-1 h-full canvas-transition"}
          style={canvasModeActive ? { width: `${chatPanelWidth}%` } : undefined}
        >
          <ChatContainer 
            ref={chatContainerRef}
            threadId={currentThreadId}
            onUpdateThreadTitle={updateThreadTitle}
            onRefreshThreads={refreshThreads}
            onArtifactDetected={handleArtifactDetected}
            onEnableCanvas={activateCanvas}
            canvasModeActive={canvasModeActive}
          />
        </div>
        {canvasModeActive && currentArtifactMessage && (
          <>
            <ResizableDivider
              onResize={handleResize}
              minLeftWidth={20}
              maxLeftWidth={70}
              initialLeftWidth={chatPanelWidth}
            />
            <div 
              className="h-full overflow-hidden"
              style={{ width: `${100 - chatPanelWidth}%` }}
            >
              <ArtifactPanel 
                message={currentArtifactMessage} 
                onClose={handleCloseCanvas}
              />
            </div>
          </>
        )}
      </div>
    </Layout>
  );
}
