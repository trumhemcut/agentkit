'use client';

import { useEffect } from 'react';
import { AgentSettingsCard } from './agent-settings-card';
import { useSettingsStore } from '@/stores/settingsStore';
import { Loader2, Settings } from 'lucide-react';

/**
 * AgentSettingsList Component
 * 
 * Displays a list of all agent settings with loading and empty states
 */
export function AgentSettingsList() {
  const { agents, loading, loadAgents } = useSettingsStore();

  useEffect(() => {
    if (agents.length === 0 && !loading) {
      loadAgents();
    }
  }, [agents.length, loading, loadAgents]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-16">
        <Loader2 className="h-8 w-8 animate-spin text-primary mb-4" />
        <p className="text-sm text-muted-foreground">Loading agent settings...</p>
      </div>
    );
  }

  if (agents.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <div className="rounded-full bg-muted p-4 mb-4">
          <Settings className="h-8 w-8 text-muted-foreground" />
        </div>
        <h3 className="text-lg font-semibold mb-2">No agents configured</h3>
        <p className="text-sm text-muted-foreground max-w-md">
          There are no agents available to configure. Agents will appear here once they are registered in the system.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {agents.map((agent) => (
        <AgentSettingsCard key={agent.id} agent={agent} />
      ))}
    </div>
  );
}
