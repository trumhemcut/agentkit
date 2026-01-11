'use client';

import { ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useRouter } from 'next/navigation';
import { ProviderSettings } from './ProviderSettings';
import { ModelSettings } from './ModelSettings';
import { AgentSettings } from './AgentSettings';
import { SystemPromptSettings } from './SystemPromptSettings';

/**
 * SettingsLayout Component
 * 
 * Main container for all settings sections.
 * Displays in a mobile-friendly, responsive layout.
 */
export function SettingsLayout() {
  const router = useRouter();

  return (
    <div className="h-full w-full overflow-y-auto bg-background">
      {/* Header */}
      <div className="sticky top-0 z-10 border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => router.back()}
              className="h-9 w-9"
              title="Back"
            >
              <ArrowLeft className="h-5 w-5" />
            </Button>
            <div>
              <h1 className="text-2xl font-semibold">Settings</h1>
              <p className="text-sm text-muted-foreground">
                Configure your agent preferences
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Settings Content */}
      <div className="container max-w-4xl mx-auto px-4 py-6 space-y-6">
        {/* Provider Settings */}
        <ProviderSettings />

        {/* Model Settings */}
        <ModelSettings />

        {/* Agent Settings */}
        <AgentSettings />

        {/* System Prompt Settings */}
        <SystemPromptSettings />
      </div>
    </div>
  );
}
