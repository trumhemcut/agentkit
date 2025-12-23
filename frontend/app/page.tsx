'use client';

import { useRef } from 'react';
import { Layout } from '@/components/Layout';
import { Sidebar } from '@/components/Sidebar';
import { ChatContainer, ChatContainerRef } from '@/components/ChatContainer';
import { useChatThreads } from '@/hooks/useChatThreads';
import { useSidebar } from '@/hooks/useSidebar';

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

  const { isCollapsed, toggleCollapse } = useSidebar();
  const chatContainerRef = useRef<ChatContainerRef>(null);
  
  const handleNewChat = () => {
    // Only create a new thread if the current thread has messages
    const hasMessages = currentThread && currentThread.messages.length > 0;
    
    if (hasMessages) {
      createThread();
    }
    
    // Focus on input after a short delay to ensure the component is rendered
    setTimeout(() => {
      chatContainerRef.current?.focusInput();
    }, 100);
  };

  return (
    <Layout
      sidebar={
        <Sidebar
          threads={threads}
          currentThreadId={currentThreadId}
          isCollapsed={isCollapsed}
          onToggleCollapse={toggleCollapse}
          onNewChat={handleNewChat}
          onSelectThread={selectThread}
          onDeleteThread={deleteThread}
        />
      }
    >
      <ChatContainer 
        ref={chatContainerRef}
        threadId={currentThreadId}
        onUpdateThreadTitle={updateThreadTitle}
        onRefreshThreads={refreshThreads}
      />
    </Layout>
  );
}
