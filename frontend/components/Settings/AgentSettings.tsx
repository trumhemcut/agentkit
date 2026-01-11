'use client';

import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { MessageCircle, Layout, LayoutGrid, Shield, Check } from 'lucide-react';
import { useAgentStore } from '@/stores/agentStore';
import { cn } from '@/lib/utils';

/**
 * AgentSettings Component
 * 
 * Allows users to select their active agent
 */
export function AgentSettings() {
  const selectedAgent = useAgentStore((state) => state.selectedAgent);
  const availableAgents = useAgentStore((state) => state.availableAgents);
  const setSelectedAgent = useAgentStore((state) => state.setSelectedAgent);
  const loading = useAgentStore((state) => state.loading);

  // Map icon names to lucide icons
  const getIcon = (iconName: string) => {
    switch (iconName) {
      case 'message-circle':
        return MessageCircle;
      case 'layout':
        return Layout;
      case 'layout-grid':
        return LayoutGrid;
      case 'shield':
        return Shield;
      default:
        return MessageCircle;
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Agent</CardTitle>
        <CardDescription>
          Select the agent to use for your conversations
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {availableAgents.map((agent) => {
            const Icon = getIcon(agent.icon);
            const isSelected = selectedAgent === agent.id;
            
            return (
              <Button
                key={agent.id}
                variant="outline"
                disabled={loading}
                onClick={() => setSelectedAgent(agent.id)}
                className={cn(
                  "w-full justify-start h-auto p-4 relative",
                  isSelected && "border-primary bg-primary/5"
                )}
              >
                <div className="flex items-center gap-3 w-full">
                  <div className={cn(
                    "flex h-10 w-10 items-center justify-center rounded-lg",
                    isSelected ? "bg-primary/10" : "bg-muted"
                  )}>
                    <Icon className={cn(
                      "h-5 w-5",
                      isSelected ? "text-primary" : "text-muted-foreground"
                    )} />
                  </div>
                  <div className="flex-1 text-left">
                    <div className="font-medium">{agent.name}</div>
                    <div className="text-xs text-muted-foreground">{agent.description}</div>
                  </div>
                  {isSelected && (
                    <Check className="h-5 w-5 text-primary" />
                  )}
                </div>
              </Button>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
