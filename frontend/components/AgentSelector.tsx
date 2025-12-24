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
      <Button variant="outline" className="min-w-[180px] justify-start" disabled>
        <MessageCircle className="h-4 w-4 mr-2" />
        <span>Loading...</span>
      </Button>
    );
  }
  
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" className="min-w-[180px] justify-between">
          <div className="flex items-center">
            {currentAgent && (
              <>
                {getIcon(currentAgent.icon)}
                <span>{currentAgent.name}</span>
              </>
            )}
          </div>
          <ChevronDown className="h-4 w-4 ml-2 opacity-50" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-[280px]">
        {availableAgents.map((agent) => (
          <DropdownMenuItem
            key={agent.id}
            onClick={() => setSelectedAgent(agent.id)}
            className="flex flex-col items-start gap-1 py-3"
          >
            <div className="flex items-center">
              {getIcon(agent.icon)}
              <span className="font-medium">{agent.name}</span>
            </div>
            <span className="text-sm text-muted-foreground pl-6">
              {agent.description}
            </span>
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
