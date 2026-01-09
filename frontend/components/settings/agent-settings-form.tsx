'use client';

import { useState } from 'react';
import { AgentSettings, AgentSettingsFormData } from '@/types/settings';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { AVAILABLE_MODELS } from '@/services/settings-mock';
import { useSettingsStore } from '@/stores/settingsStore';
import { Save, X } from 'lucide-react';

interface AgentSettingsFormProps {
  agent: AgentSettings;
  onClose?: () => void;
}

/**
 * AgentSettingsForm Component
 * 
 * Form for editing agent configuration settings
 */
export function AgentSettingsForm({ agent, onClose }: AgentSettingsFormProps) {
  const updateAgent = useSettingsStore((state) => state.updateAgent);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [formData, setFormData] = useState<AgentSettingsFormData>({
    name: agent.name,
    description: agent.description,
    enabled: agent.enabled,
    model: agent.configuration.model,
    provider: agent.configuration.provider,
    temperature: agent.configuration.temperature,
    maxTokens: agent.configuration.maxTokens,
    customInstructions: agent.configuration.customInstructions,
    systemPrompt: agent.configuration.systemPrompt,
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      await updateAgent(agent.id, {
        name: formData.name,
        description: formData.description,
        enabled: formData.enabled,
        configuration: {
          ...agent.configuration,
          model: formData.model,
          provider: formData.provider,
          temperature: formData.temperature,
          maxTokens: formData.maxTokens,
          customInstructions: formData.customInstructions,
          systemPrompt: formData.systemPrompt,
        },
      });

      if (onClose) {
        onClose();
      }
    } catch (error) {
      console.error('Failed to update agent:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReset = () => {
    setFormData({
      name: agent.name,
      description: agent.description,
      enabled: agent.enabled,
      model: agent.configuration.model,
      provider: agent.configuration.provider,
      temperature: agent.configuration.temperature,
      maxTokens: agent.configuration.maxTokens,
      customInstructions: agent.configuration.customInstructions,
      systemPrompt: agent.configuration.systemPrompt,
    });
  };

  const availableModels = formData.provider 
    ? AVAILABLE_MODELS[formData.provider] || []
    : [];

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Agent Name */}
        <div className="space-y-2">
          <Label htmlFor="name">Agent Name</Label>
          <Input
            id="name"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            placeholder="Enter agent name"
            required
          />
        </div>

        {/* Provider */}
        <div className="space-y-2">
          <Label htmlFor="provider">LLM Provider</Label>
          <Select
            value={formData.provider}
            onValueChange={(value) => {
              const newProvider = value as AgentSettingsFormData['provider'];
              const modelsForNewProvider = newProvider ? (AVAILABLE_MODELS[newProvider] || []) : [];
              setFormData({ 
                ...formData, 
                provider: newProvider,
                model: modelsForNewProvider.length > 0 ? modelsForNewProvider[0] : ''
              });
            }}
          >
            <SelectTrigger id="provider">
              <SelectValue placeholder="Select provider" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ollama">Ollama</SelectItem>
              <SelectItem value="openai">OpenAI</SelectItem>
              <SelectItem value="anthropic">Anthropic</SelectItem>
              <SelectItem value="gemini">Gemini</SelectItem>
              <SelectItem value="azure">Azure</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Model */}
        <div className="space-y-2">
          <Label htmlFor="model">Model</Label>
          <Select
            value={formData.model}
            onValueChange={(value) => setFormData({ ...formData, model: value })}
            disabled={!formData.provider || availableModels.length === 0}
          >
            <SelectTrigger id="model">
              <SelectValue placeholder="Select model" />
            </SelectTrigger>
            <SelectContent>
              {availableModels.map((model) => (
                <SelectItem key={model} value={model}>
                  {model}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Temperature */}
        <div className="space-y-2">
          <Label htmlFor="temperature">
            Temperature
            <span className="text-xs text-muted-foreground ml-2">
              ({formData.temperature?.toFixed(1) || '0.7'})
            </span>
          </Label>
          <Input
            id="temperature"
            type="number"
            min="0"
            max="2"
            step="0.1"
            value={formData.temperature || 0.7}
            onChange={(e) => setFormData({ 
              ...formData, 
              temperature: parseFloat(e.target.value) 
            })}
          />
        </div>

        {/* Max Tokens */}
        <div className="space-y-2">
          <Label htmlFor="maxTokens">Max Tokens</Label>
          <Input
            id="maxTokens"
            type="number"
            min="1"
            max="32000"
            step="1"
            value={formData.maxTokens || 2048}
            onChange={(e) => setFormData({ 
              ...formData, 
              maxTokens: parseInt(e.target.value) 
            })}
          />
        </div>
      </div>

      {/* Description */}
      <div className="space-y-2">
        <Label htmlFor="description">Description</Label>
        <Textarea
          id="description"
          value={formData.description}
          onChange={(e) => setFormData({ ...formData, description: e.target.value })}
          placeholder="Enter agent description"
          rows={2}
        />
      </div>

      {/* System Prompt */}
      <div className="space-y-2">
        <Label htmlFor="systemPrompt">System Prompt</Label>
        <Textarea
          id="systemPrompt"
          value={formData.systemPrompt || ''}
          onChange={(e) => setFormData({ ...formData, systemPrompt: e.target.value })}
          placeholder="Enter system prompt"
          rows={3}
        />
      </div>

      {/* Custom Instructions */}
      <div className="space-y-2">
        <Label htmlFor="customInstructions">Custom Instructions</Label>
        <Textarea
          id="customInstructions"
          value={formData.customInstructions || ''}
          onChange={(e) => setFormData({ ...formData, customInstructions: e.target.value })}
          placeholder="Enter custom instructions"
          rows={3}
        />
      </div>

      {/* Action Buttons */}
      <div className="flex items-center justify-end gap-2 pt-4 border-t">
        <Button
          type="button"
          variant="outline"
          onClick={handleReset}
          disabled={isSubmitting}
        >
          <X className="h-4 w-4 mr-2" />
          Reset
        </Button>
        <Button
          type="submit"
          disabled={isSubmitting}
        >
          <Save className="h-4 w-4 mr-2" />
          {isSubmitting ? 'Saving...' : 'Save Changes'}
        </Button>
      </div>
    </form>
  );
}
