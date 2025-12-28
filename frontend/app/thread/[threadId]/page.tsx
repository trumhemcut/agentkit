import { ClientChatAppLoader } from '@/components/ClientChatAppLoader';

interface ThreadPageProps {
  params: Promise<{
    threadId: string;
  }>;
}

export default async function ThreadPage({ params }: ThreadPageProps) {
  const { threadId } = await params;
  
  return <ClientChatAppLoader threadId={threadId} />;
}
