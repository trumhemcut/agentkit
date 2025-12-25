import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { useAgentSelection } from '@/hooks/useAgentSelection';
import { MessageCircle, Layout, ChevronDown } from 'lucide-react';

/**
 * Agent selector component
 * 
 * Dropdown to select active agent for chat
 * Positioned in header similar to model selector
 */
export function AgentSelector() {
  const { selectedAgent, availableAgents, setSelectedAgent, loading } = useAgentSelection();
  
  // Map icon names to lucide icons
  const getIcon = (iconName: string) => {
    switch (iconName) {
      case 'message-circle':
        return <MessageCircle className="h-4 w-4 mr-2" />;
      case 'layout':
        return <Layout className="h-4 w-4 mr-2" />;
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
            className="flex items-start gap-2 py-2 cursor-pointer"
          >
            <div className="flex items-center">
              {getIcon(agent.icon)}
            </div>
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
