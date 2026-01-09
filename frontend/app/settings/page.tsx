'use client';

import { Settings as SettingsIcon } from 'lucide-react';
import { AgentSettingsList } from '@/components/settings/agent-settings-list';

/**
 * Settings Page
 * 
 * Admin page for configuring agent settings
 */
export default function SettingsPage() {
  return (
    <div className="flex flex-col h-screen overflow-hidden">
      {/* Header */}
      <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-16 items-center px-4 md:px-8">
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-primary/10 p-2">
              <SettingsIcon className="h-5 w-5 text-primary" />
            </div>
            <div>
              <h1 className="text-xl font-semibold">Settings</h1>
              <p className="text-sm text-muted-foreground">
                Configure agent settings and behavior
              </p>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        <div className="container py-6 px-4 md:px-8 max-w-5xl">
          <div className="space-y-6">
            {/* Section Header */}
            <div>
              <h2 className="text-lg font-semibold mb-1">Agent Configuration</h2>
              <p className="text-sm text-muted-foreground">
                Manage agent settings including models, parameters, and behavior customization
              </p>
            </div>

            {/* Agent Settings List */}
            <AgentSettingsList />
          </div>
        </div>
      </main>
    </div>
  );
}
