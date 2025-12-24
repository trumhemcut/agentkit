'use client';

import { useRef, useCallback } from 'react';
import { Layout } from '@/components/Layout';
import { Sidebar } from '@/components/Sidebar';
import { ChatContainer, ChatContainerRef } from '@/components/ChatContainer';
import { ArtifactPanel } from '@/components/ArtifactPanel';
import { useChatThreads } from '@/hooks/useChatThreads';
import { useSidebar } from '@/hooks/useSidebar';
import { useCanvasMode } from '@/hooks/useCanvasMode';
import { Message } from '@/types/chat';

export default function Home() {
  const {
    threads,
    currentThread,
    currentThreadId,
    createThread,
    deleteThread,
    selectThread,
    updateThreadTitle,
    refreshThreads,
  } = useChatThreads();

  const { isCollapsed, toggleCollapse, setCollapsed } = useSidebar();
  const { 
    isActive: canvasModeActive, 
    currentArtifactMessage,
    activateCanvas,
    deactivateCanvas,
    updateCurrentArtifact,
  } = useCanvasMode();
  
  const chatContainerRef = useRef<ChatContainerRef>(null);
  
  // Handle artifact detection from messages
  const handleArtifactDetected = useCallback((message: Message) => {
    console.log('[Home] Artifact detected, activating canvas mode:', message);
    activateCanvas(message);
    setCollapsed(true); // Collapse sidebar when canvas mode activates
  }, [activateCanvas, setCollapsed]);
  
  const handleNewChat = () => {
    // Only create a new thread if the current thread has messages
    const hasMessages = currentThread && currentThread.messages.length > 0;
    
    if (hasMessages) {
      createThread();
      // Deactivate canvas mode when starting a new chat
      deactivateCanvas();
    }
    
    // Focus on input after a short delay to ensure the component is rendered
    setTimeout(() => {
      chatContainerRef.current?.focusInput();
    }, 100);
  };
  
  const handleCloseCanvas = () => {
    deactivateCanvas();
    setCollapsed(false); // Restore sidebar when canvas closes
  };

  return (
    <Layout
      sidebar={
        <Sidebar
          threads={threads}
          currentThreadId={currentThreadId}
          isCollapsed={isCollapsed || canvasModeActive}
          onToggleCollapse={toggleCollapse}
          onNewChat={handleNewChat}
          onSelectThread={selectThread}
          onDeleteThread={deleteThread}
        />
      }
    >
      <div className={canvasModeActive ? "grid grid-cols-3 h-full gap-0 canvas-grid-layout" : "flex h-full canvas-transition"}>
        <div className={canvasModeActive ? "col-span-1 border-r h-full overflow-hidden canvas-transition" : "flex-1 h-full canvas-transition"}>
          <ChatContainer 
            ref={chatContainerRef}
            threadId={currentThreadId}
            onUpdateThreadTitle={updateThreadTitle}
            onRefreshThreads={refreshThreads}
            onArtifactDetected={handleArtifactDetected}
            onEnableCanvas={activateCanvas}
          />
        </div>
        {canvasModeActive && currentArtifactMessage && (
          <div className="col-span-2 h-full overflow-hidden">
            <ArtifactPanel 
              message={currentArtifactMessage} 
              onClose={handleCloseCanvas}
            />
          </div>
        )}
      </div>
    </Layout>
  );
}
