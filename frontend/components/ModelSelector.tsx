/**
 * ModelSelector Component
 * 
 * Dropdown menu for selecting LLM models. Positioned similar to ChatGPT's model selector.
 * Uses Shadcn UI DropdownMenu component with model list, size information, and availability status.
 */

"use client";

import React from 'react';
import { Bot, Check, ChevronDown, Loader2 } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Button } from '@/components/ui/button';
import { useModelSelection } from '@/hooks/useModelSelection';
import { cn } from '@/lib/utils';

export function ModelSelector() {
  const {
    models,
    selectedModel,
    selectedModelInfo,
    loading,
    error,
    selectModel,
  } = useModelSelection();

  // Show loading state
  if (loading) {
    return (
      <Button variant="ghost" size="sm" disabled className="gap-2">
        <Loader2 className="h-4 w-4 animate-spin" />
        <span className="hidden sm:inline">Loading models...</span>
      </Button>
    );
  }

  // Show error state
  if (error || models.length === 0) {
    return (
      <Button variant="ghost" size="sm" disabled className="gap-2">
        <Bot className="h-4 w-4" />
        <span className="hidden sm:inline">No models available</span>
      </Button>
    );
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="sm" className="gap-2">
          <Bot className="h-4 w-4" />
          <span className="hidden sm:inline">
            {selectedModelInfo?.name || 'Select Model'}
          </span>
          <ChevronDown className="h-4 w-4" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-[240px]">
        <DropdownMenuLabel>Select Model</DropdownMenuLabel>
        <DropdownMenuSeparator />
        {models.map((model) => (
          <DropdownMenuItem
            key={model.id}
            onClick={() => selectModel(model.id)}
            disabled={!model.available}
            className={cn(
              "flex items-start gap-2 py-2 cursor-pointer",
              !model.available && "opacity-50 cursor-not-allowed"
            )}
          >
            <div className="flex h-5 w-5 items-center justify-center">
              {selectedModel === model.id && (
                <Check className="h-4 w-4" />
              )}
            </div>
            <div className="flex flex-col gap-0.5">
              <span className="font-medium">{model.name}</span>
              <span className="text-xs text-muted-foreground">
                {model.size}
              </span>
              {!model.available && (
                <span className="text-xs text-destructive">
                  Not available
                </span>
              )}
            </div>
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
