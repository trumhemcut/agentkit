'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { StorageService } from '@/services/storage';
import { threadsApi } from '@/services/api';

export function HomeRedirect() {
  const router = useRouter();
  
  useEffect(() => {
    const initializeThread = async () => {
      // Get threads from localStorage
      const threads = StorageService.getThreads();
      
      if (threads.length > 0) {
        // Redirect to most recent thread
        router.replace(`/t/${threads[0].id}`);
      } else {
        // Create new thread with server-authoritative ID
        try {
          const serverThread = await threadsApi.create({
            agent_id: 'chat',
            model: 'qwen:7b',
            provider: 'ollama',
            title: 'New Chat',
          });
          
          // Save to localStorage with server ID
          const newThread = {
            id: serverThread.id,
            title: serverThread.title,
            messages: [],
            createdAt: new Date(serverThread.created_at).getTime(),
            updatedAt: new Date(serverThread.updated_at).getTime(),
          };
          StorageService.saveThread(newThread);
          router.replace(`/t/${serverThread.id}`);
        } catch (error) {
          console.error('Failed to create thread:', error);
          // Fallback to temp thread if server fails
          const tempThread = {
            id: crypto.randomUUID(),
            title: 'New Chat',
            messages: [],
            createdAt: Date.now(),
            updatedAt: Date.now(),
          };
          StorageService.saveThread(tempThread);
          router.replace(`/t/${tempThread.id}`);
        }
      }
    };
    
    initializeThread();
  }, [router]);
  
  // Show loading while redirecting
  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto mb-4"></div>
        <p className="text-gray-600">Loading...</p>
      </div>
    </div>
  );
}
