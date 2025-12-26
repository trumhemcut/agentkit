import { ModelSelector } from './ModelSelector';
import { AgentSelector } from './AgentSelector';
import { ProviderSelector } from './ProviderSelector';

/**
 * Header component
 * 
 * Application header with agent, provider, and model selectors
 */
export function Header() {
  return (
    <header className="bg-background shadow-sm">
      <div className="flex h-16 items-center px-6 justify-start gap-4">
        <AgentSelector />
        <ProviderSelector />
        <ModelSelector />
      </div>
    </header>
  );
}
