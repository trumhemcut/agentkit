'use client';

import { ReactNode } from 'react';
import { Header } from './Header';

interface LayoutProps {
  sidebar: ReactNode;
  children: ReactNode;
}

/**
 * Main Layout component
 * 
 * Composes header, sidebar, and main content area with full-height layout
 */
export function Layout({ sidebar, children }: LayoutProps) {
  return (
    <div className="flex h-screen overflow-hidden">
      {sidebar}
      <div className="flex flex-1 flex-col overflow-hidden relative">
        <Header />
        <main className="flex-1 overflow-hidden relative z-10">
          {children}
        </main>
      </div>
    </div>
  );
}
