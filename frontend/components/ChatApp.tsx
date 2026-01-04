'use client';

import { useRef, useCallback, useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import dynamic from 'next/dynamic';
import { Layout } from '@/components/Layout';
import { Sidebar } from '@/components/Sidebar';
import { ChatContainer, ChatContainerRef } from '@/components/ChatContainer';
import { MobileTabNavigation, MobileTab } from '@/components/MobileTabNavigation';
import { useChatThreads } from '@/hooks/useChatThreads';
import { useSidebar } from '@/hooks/useSidebar';
import { useCanvasMode } from '@/hooks/useCanvasMode';
import { useIsMobile } from '@/hooks/useMediaQuery';
import { useModelStore } from '@/stores/modelStore';
import { useAgentStore } from '@/stores/agentStore';
import { useMessageStore } from '@/stores/messageStore';
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
  
  // Get current model and agent selection for thread creation
  const selectedModel = useModelStore((state) => state.selectedModel);
  const selectedProvider = useModelStore((state) => state.selectedProvider);
  const selectedAgent = useAgentStore((state) => state.selectedAgent);
  
  const {
    threads,
    currentThread,
    currentThreadId,
    createThread,
    deleteThread,
    selectThread,
    updateThreadTitle,
    refreshThreads,
  } = useChatThreads(
    initialThreadId,
    selectedAgent || 'chat',
    selectedModel || 'qwen:7b',
    selectedProvider || 'ollama'
  );

  const { isCollapsed, toggleCollapse, setCollapsed, isMobileOpen, openMobileDrawer, closeMobileDrawer, toggleMobileDrawer } = useSidebar();
  const { 
    isActive: canvasModeActive, 
    currentArtifactMessage,
    activateCanvas,
    deactivateCanvas,
    updateCurrentArtifact,
  } = useCanvasMode();
  
  const isMobile = useIsMobile();
  const [mobileTab, setMobileTab] = useState<MobileTab>('chat');
  
  const chatContainerRef = useRef<ChatContainerRef>(null);
  const isCreatingNewThreadRef = useRef(false);
  
  // Resizable panel widths (in percentages)
  const [chatPanelWidth, setChatPanelWidth] = useState(33.33);
  
  // Get canvas context to load and set artifactId
  const { setArtifactId, loadArtifactById } = useCanvas();
  
  // Get message store to check if thread has messages
  const { getMessages } = useMessageStore();
  
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
    
    // Auto-collapse sidebar on desktop, switch to canvas tab on mobile
    if (isMobile) {
      setMobileTab('canvas');
    } else {
      setCollapsed(true);
    }
  }, [activateCanvas, setArtifactId, loadArtifactById, setCollapsed, isMobile]);
  
  const handleNewChat = useCallback(async () => {
    // Mark that we're creating a new thread
    isCreatingNewThreadRef.current = true;
    
    // Deactivate canvas mode first
    deactivateCanvas();
    
    // Create a new thread if there's no current thread or if the current thread has messages
    const hasNoThread = !currentThread;
    const hasMessages = currentThreadId && getMessages(currentThreadId).length > 0;
    
    if (hasNoThread || hasMessages) {
      const newThread = await createThread();
      
      // Only update URL if thread was created successfully
      if (newThread && newThread.id) {
        // Update URL without causing full navigation
        // This prevents component remount and sidebar state changes
        window.history.pushState({}, '', `/t/${newThread.id}`);
      }
      
      // Clear the flag after state updates complete
      requestAnimationFrame(() => {
        isCreatingNewThreadRef.current = false;
        // Focus input after DOM updates
        chatContainerRef.current?.focusInput();
      });
    } else {
      // If current thread is empty, just focus input
      isCreatingNewThreadRef.current = false;
      chatContainerRef.current?.focusInput();
    }
  }, [currentThread, currentThreadId, getMessages, createThread, deactivateCanvas]);

  const handleSelectThread = useCallback((threadId: string) => {
    selectThread(threadId);
    // Navigate to thread URL
    router.push(`/t/${threadId}`);
  }, [selectThread, router]);
  
  const handleCloseCanvas = () => {
    deactivateCanvas();
    // Restore sidebar on desktop, switch to chat tab on mobile
    if (isMobile) {
      setMobileTab('chat');
    } else {
      setCollapsed(false);
    }
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
          isMobileOpen={isMobileOpen}
          onCloseMobile={closeMobileDrawer}
        />
      }
      onMenuClick={toggleMobileDrawer}
    >
      {/* Mobile Tab Navigation - Only shown on mobile when canvas is active */}
      {isMobile && canvasModeActive && (
        <MobileTabNavigation
          activeTab={mobileTab}
          onTabChange={setMobileTab}
          showCanvasBadge={canvasModeActive && mobileTab === 'chat'}
        />
      )}

      {/* Content Area */}
      <div className={isMobile ? "h-full" : (canvasModeActive ? "flex h-full canvas-grid-layout" : "flex h-full canvas-transition")}>
        {/* Mobile: Show only active tab */}
        {isMobile ? (
          <>
            {mobileTab === 'chat' && (
              <div className="h-full">
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
            )}
            {mobileTab === 'canvas' && canvasModeActive && currentArtifactMessage && (
              <div className="h-full">
                <ArtifactPanel
                  message={currentArtifactMessage}
                  onClose={handleCloseCanvas}
                />
              </div>
            )}
          </>
        ) : (
          /* Desktop: Side-by-side layout */
          <>
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
          </>
        )}
      </div>
    </Layout>
  );
}
