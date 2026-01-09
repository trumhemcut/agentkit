'use client';

import { useState } from 'react';
import { AgentSettings } from '@/types/settings';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { ChevronDown, ChevronUp, Bot } from 'lucide-react';
import { cn } from '@/lib/utils';
import { AgentSettingsForm } from './agent-settings-form';
import { useSettingsStore } from '@/stores/settingsStore';

interface AgentSettingsCardProps {
  agent: AgentSettings;
}

/**
 * AgentSettingsCard Component
 * 
 * Displays an individual agent's settings with expand/collapse functionality
 */
export function AgentSettingsCard({ agent }: AgentSettingsCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const updateAgent = useSettingsStore((state) => state.updateAgent);

  const handleToggleEnabled = async (enabled: boolean) => {
    await updateAgent(agent.id, { enabled });
  };

  const getAgentTypeColor = (type: string): string => {
    const colors: Record<string, string> = {
      chat: 'bg-blue-100 text-blue-800',
      canvas: 'bg-purple-100 text-purple-800',
      insurance: 'bg-green-100 text-green-800',
      salary_viewer: 'bg-yellow-100 text-yellow-800',
      a2ui: 'bg-pink-100 text-pink-800',
      custom: 'bg-gray-100 text-gray-800',
    };
    return colors[type] || colors.custom;
  };

  return (
    <Card className={cn(
      "transition-all duration-200",
      !agent.enabled && "opacity-60"
    )}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-3 flex-1">
            <div className={cn(
              "mt-1 rounded-lg p-2",
              agent.enabled ? "bg-primary/10" : "bg-gray-100"
            )}>
              <Bot className={cn(
                "h-5 w-5",
                agent.enabled ? "text-primary" : "text-gray-400"
              )} />
            </div>
            <div className="flex-1 space-y-1">
              <div className="flex items-center gap-2 flex-wrap">
                <CardTitle className="text-lg">{agent.name}</CardTitle>
                <Badge variant="secondary" className={cn("text-xs", getAgentTypeColor(agent.type))}>
                  {agent.type}
                </Badge>
                {agent.enabled ? (
                  <Badge variant="default" className="bg-green-500 text-white text-xs">
                    Enabled
                  </Badge>
                ) : (
                  <Badge variant="secondary" className="text-xs">
                    Disabled
                  </Badge>
                )}
              </div>
              <CardDescription className="text-sm">
                {agent.description}
              </CardDescription>
              <div className="flex items-center gap-4 text-xs text-muted-foreground pt-1">
                <span>Model: {agent.configuration.model || 'Not set'}</span>
                <span>•</span>
                <span>Provider: {agent.configuration.provider || 'Not set'}</span>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2 ml-4">
            <div className="flex items-center gap-2">
              <Switch
                checked={agent.enabled}
                onCheckedChange={handleToggleEnabled}
                aria-label="Toggle agent enabled status"
              />
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setIsExpanded(!isExpanded)}
              aria-label={isExpanded ? "Collapse settings" : "Expand settings"}
            >
              {isExpanded ? (
                <ChevronUp className="h-4 w-4" />
              ) : (
                <ChevronDown className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>
      </CardHeader>

      {isExpanded && (
        <CardContent className="pt-0">
          <div className="border-t pt-4">
            <AgentSettingsForm agent={agent} onClose={() => setIsExpanded(false)} />
          </div>
        </CardContent>
      )}
    </Card>
  );
}
