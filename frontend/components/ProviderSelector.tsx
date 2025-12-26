"use client";

import React from 'react';
import { Cloud, Server, Check, ChevronDown } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Button } from '@/components/ui/button';
import { useModelStore } from '@/stores/modelStore';
import { cn } from '@/lib/utils';

const providerIcons: Record<string, React.ComponentType<{ className?: string }>> = {
  ollama: Server,
  gemini: Cloud,
};

export function ProviderSelector() {
  const selectedProvider = useModelStore((state) => state.selectedProvider);
  const availableProviders = useModelStore((state) => state.availableProviders);
  const setSelectedProvider = useModelStore((state) => state.setSelectedProvider);
  const loading = useModelStore((state) => state.loading);
  
  const currentProvider = availableProviders.find(p => p.id === selectedProvider);
  const Icon = currentProvider ? providerIcons[currentProvider.id] || Server : Server;
  
  if (loading) {
    return <Button variant="ghost" size="sm" disabled>Loading...</Button>;
  }
  
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="sm" className="gap-2">
          <Icon className="h-4 w-4" />
          <span className="hidden sm:inline">
            {currentProvider?.name || 'Select Provider'}
          </span>
          <ChevronDown className="h-4 w-4" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-[200px]">
        <DropdownMenuLabel>Select Provider</DropdownMenuLabel>
        <DropdownMenuSeparator />
        {availableProviders.map((provider) => {
          const ProviderIcon = providerIcons[provider.id] || Server;
          return (
            <DropdownMenuItem
              key={provider.id}
              onClick={() => setSelectedProvider(provider.id)}
              disabled={!provider.available}
              className={cn(
                "flex items-center gap-2 cursor-pointer",
                !provider.available && "opacity-50 cursor-not-allowed"
              )}
            >
              <div className="flex h-5 w-5 items-center justify-center">
                {selectedProvider === provider.id && (
                  <Check className="h-4 w-4" />
                )}
              </div>
              <ProviderIcon className="h-4 w-4" />
              <span>{provider.name}</span>
            </DropdownMenuItem>
          );
        })}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
