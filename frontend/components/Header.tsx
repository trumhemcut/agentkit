import { ModelSelector } from './ModelSelector';
import { AgentSelector } from './AgentSelector';

/**
 * Header component
 * 
 * Application header with agent and model selectors
 */
export function Header() {
  return (
    <header className="bg-background shadow-sm">
      <div className="flex h-16 items-center px-6 justify-start gap-4">
        <AgentSelector />
        <ModelSelector />
      </div>
    </header>
  );
}
