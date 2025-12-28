'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { StorageService } from '@/services/storage';

export function HomeRedirect() {
  const router = useRouter();
  
  useEffect(() => {
    // Get threads from localStorage
    const threads = StorageService.getThreads();
    
    if (threads.length > 0) {
      // Redirect to most recent thread
      router.replace(`/thread/${threads[0].id}`);
    } else {
      // Create new thread and redirect to it
      const newThread = {
        id: `thread-${Date.now()}`,
        title: 'New Chat',
        messages: [],
        createdAt: Date.now(),
        updatedAt: Date.now(),
      };
      StorageService.saveThread(newThread);
      router.replace(`/thread/${newThread.id}`);
    }
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
