/**
 * useModelSelection Hook
 * 
 * Custom hook to manage LLM model selection state, persistence, and API integration.
 * Handles fetching available models, storing user's selection in localStorage,
 * and providing model state to components.
 */

import { useState, useEffect } from 'react';
import { LLMModel, ModelsResponse } from '@/types/chat';
import { fetchAvailableModels } from '@/services/api';

const STORAGE_KEY = 'selected-llm-model';

export function useModelSelection() {
  const [models, setModels] = useState<LLMModel[]>([]);
  const [selectedModel, setSelectedModel] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Load models on mount
  useEffect(() => {
    loadModels();
  }, []);

  /**
   * Fetch available models from backend and initialize selection
   */
  const loadModels = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch models from API
      const response: ModelsResponse = await fetchAvailableModels();
      setModels(response.models);

      // Load saved model from localStorage or use default
      const savedModel = localStorage.getItem(STORAGE_KEY);
      const modelToSelect = savedModel || response.default;

      // Verify the model exists and is available
      const modelExists = response.models.find(
        m => m.id === modelToSelect && m.available
      );

      if (modelExists) {
        setSelectedModel(modelToSelect);
      } else {
        // Fall back to first available model
        const firstAvailable = response.models.find(m => m.available);
        if (firstAvailable) {
          setSelectedModel(firstAvailable.id);
          localStorage.setItem(STORAGE_KEY, firstAvailable.id);
        }
      }
    } catch (err) {
      console.error('[useModelSelection] Error loading models:', err);
      setError(err instanceof Error ? err.message : 'Failed to load models');
    } finally {
      setLoading(false);
    }
  };

  /**
   * Select a new model and persist to localStorage
   */
  const selectModel = (modelId: string) => {
    const model = models.find(m => m.id === modelId);
    
    if (!model) {
      console.error('[useModelSelection] Model not found:', modelId);
      return;
    }

    if (!model.available) {
      console.error('[useModelSelection] Model not available:', modelId);
      return;
    }

    console.log('[useModelSelection] Selecting model:', modelId);
    setSelectedModel(modelId);
    localStorage.setItem(STORAGE_KEY, modelId);
  };

  /**
   * Get the full model object for the selected model
   */
  const getSelectedModelInfo = (): LLMModel | null => {
    if (!selectedModel) return null;
    return models.find(m => m.id === selectedModel) || null;
  };

  /**
   * Refresh models from API
   */
  const refreshModels = () => {
    loadModels();
  };

  return {
    models,
    selectedModel,
    selectedModelInfo: getSelectedModelInfo(),
    loading,
    error,
    selectModel,
    refreshModels,
  };
}
