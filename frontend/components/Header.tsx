import { ModelSelector } from './ModelSelector';

/**
 * Header component
 * 
 * Application header with model selector - clean, borderless design
 */
export function Header() {
  return (
    <header className="bg-background shadow-sm">
      <div className="flex h-16 items-center px-6 justify-start">
        <ModelSelector />
      </div>
    </header>
  );
}
