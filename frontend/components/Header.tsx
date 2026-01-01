'use client';

import { Menu } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ModelSelector } from './ModelSelector';
import { AgentSelector } from './AgentSelector';
import { ProviderSelector } from './ProviderSelector';
import { useIsMobile } from '@/hooks/useMediaQuery';
import { cn } from '@/lib/utils';

interface HeaderProps {
  onMenuClick?: () => void;
}

/**
 * Header component
 * 
 * Application header with agent, provider, and model selectors.
 * On mobile (<768px), displays hamburger menu and stacks selectors vertically.
 */
export function Header({ onMenuClick }: HeaderProps) {
  const isMobile = useIsMobile();

  return (
    <header className="relative z-50 bg-background border-b border-border">
      <div className="flex h-16 items-center px-4 md:px-6 gap-2 md:gap-4">
        {/* Mobile hamburger menu */}
        {isMobile && (
          <Button
            variant="ghost"
            size="icon"
            onClick={onMenuClick}
            className="h-10 w-10 shrink-0"
            title="Open menu"
          >
            <Menu className="h-5 w-5" />
          </Button>
        )}
        
        {/* Selectors - horizontal on both mobile and desktop */}
        <div className="flex items-center gap-1 md:gap-4 flex-1">
          <AgentSelector />
          <ProviderSelector />
          <ModelSelector />
        </div>
      </div>
    </header>
  );
}
