'use client';

import { Layout } from '@/components/Layout';
import { Sidebar } from '@/components/Sidebar';
import { ChatContainer } from '@/components/ChatContainer';
import { useChatThreads } from '@/hooks/useChatThreads';

export default function Home() {
  const {
    threads,
    currentThreadId,
    createThread,
    deleteThread,
    selectThread,
    updateThreadTitle,
  } = useChatThreads();

  return (
    <Layout
      sidebar={
        <Sidebar
          threads={threads}
          currentThreadId={currentThreadId}
          onNewChat={createThread}
          onSelectThread={selectThread}
          onDeleteThread={deleteThread}
        />
      }
    >
      <ChatContainer 
        threadId={currentThreadId}
        onUpdateThreadTitle={updateThreadTitle}
      />
    </Layout>
  );
}
