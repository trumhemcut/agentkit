'use client';

import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Bot, Check } from 'lucide-react';
import { useModelStore } from '@/stores/modelStore';
import { cn } from '@/lib/utils';

/**
 * ModelSettings Component
 * 
 * Allows users to select their LLM model
 */
export function ModelSettings() {
  const selectedProvider = useModelStore((state) => state.selectedProvider);
  const selectedModel = useModelStore((state) => state.selectedModel);
  const getProviderModels = useModelStore((state) => state.getProviderModels);
  const setSelectedModel = useModelStore((state) => state.setSelectedModel);
  const loading = useModelStore((state) => state.loading);

  const availableModels = selectedProvider 
    ? getProviderModels(selectedProvider)
    : [];

  if (availableModels.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Model</CardTitle>
          <CardDescription>
            Select a provider first to see available models
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <Bot className="h-12 w-12 text-muted-foreground mb-3" />
            <p className="text-sm text-muted-foreground">No models available</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Model</CardTitle>
        <CardDescription>
          Select the language model to use for your agents
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {availableModels.map((model) => {
            const isSelected = selectedModel === model.id;
            
            return (
              <Button
                key={model.id}
                variant="outline"
                disabled={!model.available || loading}
                onClick={() => setSelectedModel(model.id)}
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
                    <Bot className={cn(
                      "h-5 w-5",
                      isSelected ? "text-primary" : "text-muted-foreground"
                    )} />
                  </div>
                  <div className="flex-1 text-left">
                    <div className="font-medium">{model.name}</div>
                    <div className="text-xs text-muted-foreground">{model.size}</div>
                    {!model.available && (
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
