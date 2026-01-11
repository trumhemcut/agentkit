'use client';

import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Cloud, Server, Check } from 'lucide-react';
import { useModelStore } from '@/stores/modelStore';
import { cn } from '@/lib/utils';

const providerIcons: Record<string, React.ComponentType<{ className?: string }>> = {
  ollama: Server,
  gemini: Cloud,
};

/**
 * ProviderSettings Component
 * 
 * Allows users to select their AI provider
 */
export function ProviderSettings() {
  const selectedProvider = useModelStore((state) => state.selectedProvider);
  const availableProviders = useModelStore((state) => state.availableProviders);
  const setSelectedProvider = useModelStore((state) => state.setSelectedProvider);
  const loading = useModelStore((state) => state.loading);

  return (
    <Card>
      <CardHeader>
        <CardTitle>AI Provider</CardTitle>
        <CardDescription>
          Select the AI provider to use for your agents
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {availableProviders.map((provider) => {
            const Icon = providerIcons[provider.id] || Server;
            const isSelected = selectedProvider === provider.id;
            
            return (
              <Button
                key={provider.id}
                variant="outline"
                disabled={!provider.available || loading}
                onClick={() => setSelectedProvider(provider.id)}
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
                    <div className="font-medium">{provider.name}</div>
                    {!provider.available && (
                      <div className="text-xs text-destructive">Not available</div>
                    )}
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
