import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { useAgentStore, initializeAgentStore } from '@/stores/agentStore';
import { MessageCircle, Layout, Shield, LayoutGrid, ChevronDown } from 'lucide-react';
import { useEffect } from 'react';

/**
 * Agent selector component
 * 
 * Dropdown to select active agent for chat
 * Positioned in header similar to model selector
 */
export function AgentSelector() {
  // Auto-initialize store on mount
  useEffect(() => {
    initializeAgentStore();
  }, []);

  // Selective subscriptions for better performance
  const selectedAgent = useAgentStore((state) => state.selectedAgent);
  const availableAgents = useAgentStore((state) => state.availableAgents);
  const setSelectedAgent = useAgentStore((state) => state.setSelectedAgent);
  const loading = useAgentStore((state) => state.loading);
  
  // Map icon names to lucide icons
  const getIcon = (iconName: string) => {
    switch (iconName) {
      case 'message-circle':
        return <MessageCircle className="h-4 w-4 mr-2" />;
      case 'layout':
        return <Layout className="h-4 w-4 mr-2" />;
      case 'layout-grid':
        return <LayoutGrid className="h-4 w-4 mr-2" />;
      case 'shield':
        return <Shield className="h-4 w-4 mr-2" />;
      default:
        return <MessageCircle className="h-4 w-4 mr-2" />;
    }
  };
  
  const currentAgent = availableAgents.find(a => a.id === selectedAgent);
  
  if (loading) {
    return (
      <Button variant="ghost" size="sm" disabled className="gap-2">
        <MessageCircle className="h-4 w-4" />
        <span className="hidden sm:inline">Loading agents...</span>
      </Button>
    );
  }
  
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="sm" className="gap-2">
          {currentAgent && getIcon(currentAgent.icon)}
          <span className="hidden sm:inline">
            {currentAgent?.name || 'Select Agent'}
          </span>
          <ChevronDown className="h-4 w-4" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-[240px]">
        {availableAgents.map((agent) => (
          <DropdownMenuItem
            key={agent.id}
            onClick={() => setSelectedAgent(agent.id)}
          >
            {getIcon(agent.icon)}
            <div className="flex flex-col gap-0.5">
              <span className="font-medium">{agent.name}</span>
              <span className="text-xs text-muted-foreground">
                {agent.description}
              </span>
            </div>
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
