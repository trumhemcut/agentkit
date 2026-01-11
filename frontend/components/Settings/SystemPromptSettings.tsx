'use client';

import { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { RotateCcw, Save, Check } from 'lucide-react';
import { toast } from 'sonner';

const DEFAULT_SYSTEM_PROMPT = `You are a helpful AI assistant. You provide clear, accurate, and concise responses to user queries.`;

/**
 * SystemPromptSettings Component
 * 
 * Allows users to customize system prompts for their agents
 */
export function SystemPromptSettings() {
  const [systemPrompt, setSystemPrompt] = useState('');
  const [savedPrompt, setSavedPrompt] = useState('');
  const [hasChanges, setHasChanges] = useState(false);

  // Load saved prompt from localStorage
  useEffect(() => {
    const saved = localStorage.getItem('system-prompt');
    const prompt = saved || DEFAULT_SYSTEM_PROMPT;
    setSystemPrompt(prompt);
    setSavedPrompt(prompt);
  }, []);

  // Check for changes
  useEffect(() => {
    setHasChanges(systemPrompt !== savedPrompt);
  }, [systemPrompt, savedPrompt]);

  const handleSave = () => {
    localStorage.setItem('system-prompt', systemPrompt);
    setSavedPrompt(systemPrompt);
    setHasChanges(false);
    toast.success('System prompt saved successfully');
  };

  const handleReset = () => {
    setSystemPrompt(DEFAULT_SYSTEM_PROMPT);
  };

  const handleCancel = () => {
    setSystemPrompt(savedPrompt);
  };

  const characterCount = systemPrompt.length;

  return (
    <Card>
      <CardHeader>
        <CardTitle>System Prompt</CardTitle>
        <CardDescription>
          Customize the system prompt for your agents
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="system-prompt">Prompt</Label>
          <Textarea
            id="system-prompt"
            value={systemPrompt}
            onChange={(e) => setSystemPrompt(e.target.value)}
            placeholder="Enter your system prompt..."
            className="min-h-[120px] resize-y"
          />
          <div className="flex justify-between items-center text-xs text-muted-foreground">
            <span>{characterCount} characters</span>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleReset}
              className="h-7 text-xs"
            >
              <RotateCcw className="h-3 w-3 mr-1" />
              Reset to default
            </Button>
          </div>
        </div>

        {hasChanges && (
          <div className="flex gap-2 pt-2">
            <Button
              onClick={handleSave}
              size="sm"
              className="flex-1"
            >
              <Save className="h-4 w-4 mr-2" />
              Save Changes
            </Button>
            <Button
              onClick={handleCancel}
              variant="outline"
              size="sm"
              className="flex-1"
            >
              Cancel
            </Button>
          </div>
        )}

        {!hasChanges && savedPrompt && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Check className="h-4 w-4 text-green-600" />
            <span>Saved</span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
