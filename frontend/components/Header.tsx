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
    <header className="relative z-50 bg-background border-b border-border">
      <div className="flex h-16 items-center px-6 justify-start gap-4">
        <AgentSelector />
        <ProviderSelector />
        <ModelSelector />
      </div>
    </header>
  );
}
