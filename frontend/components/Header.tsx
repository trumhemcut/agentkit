import { Bot } from 'lucide-react';

/**
 * Header component
 * 
 * Application header with title and branding - clean, borderless design
 */
export function Header() {
  return (
    <header className="bg-background shadow-sm">
      <div className="flex h-16 items-center px-6">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <Bot className="h-6 w-6" />
          </div>
          <div>
            <h1 className="text-xl font-bold">AgentKit</h1>
            <p className="text-xs text-muted-foreground">Multi-Agent AI Assistant</p>
          </div>
        </div>
      </div>
    </header>
  );
}
