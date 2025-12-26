/**
 * Model Store - Zustand
 * 
 * Global store for managing LLM model selection state
 * Uses Zustand with persist middleware for localStorage sync
 */

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { LLMModel, LLMProvider, ModelsResponse } from '@/types/chat';
import { fetchAvailableModels } from '@/services/api';

const MODEL_STORAGE_KEY = 'selected-llm-model';

interface ModelStore {
  // State
  selectedProvider: string | null;  // Selected provider (e.g., "ollama", "gemini")
  selectedModel: string | null;
  availableProviders: LLMProvider[];  // Available providers
  availableModels: LLMModel[];
  loading: boolean;
  error: string | null;
  
  // Actions
  setSelectedProvider: (providerId: string) => void;
  setSelectedModel: (modelId: string) => void;
  getProviderModels: (providerId: string) => LLMModel[];  // Filter models by provider
  loadModels: () => Promise<void>;
  getSelectedModelInfo: () => LLMModel | null;
  reset: () => void;
}

export const useModelStore = create<ModelStore>()(
  persist(
    (set, get) => ({
      // Initial state
      selectedProvider: null,
      selectedModel: null,
      availableProviders: [],
      availableModels: [],
      loading: false,
      error: null,
      
      // Set provider and auto-select first available model
      setSelectedProvider: (providerId: string) => {
        const { availableProviders } = get();
        const provider = availableProviders.find(p => p.id === providerId);
        
        if (!provider || !provider.available) {
          console.error('[ModelStore] Provider not available:', providerId);
          return;
        }
        
        console.log('[ModelStore] Setting provider to:', providerId);
        
        // Get models for this provider
        const providerModels = get().getProviderModels(providerId);
        
        // Auto-select first available model
        const firstModel = providerModels.find(m => m.available);
        
        set({ 
          selectedProvider: providerId,
          selectedModel: firstModel?.id || null
        });
      },
      
      // Get models filtered by provider
      getProviderModels: (providerId: string) => {
        const { availableModels } = get();
        return availableModels.filter(m => m.provider === providerId);
      },
      
      // Actions
      setSelectedModel: (modelId: string) => {
        const { availableModels } = get();
        const model = availableModels.find(m => m.id === modelId);
        
        if (!model) {
          console.error('[ModelStore] Model not found:', modelId);
          return;
        }
        
        if (!model.available) {
          console.error('[ModelStore] Model not available:', modelId);
          return;
        }
        
        console.log('[ModelStore] Setting model to:', modelId);
        set({ selectedModel: modelId });
      },
      
      loadModels: async () => {
        const { loading } = get();
        if (loading) return; // Prevent duplicate loads
        
        try {
          set({ loading: true, error: null });
          console.log('[ModelStore] Loading models...');
          
          const response: ModelsResponse = await fetchAvailableModels();
          console.log('[ModelStore] Loaded models from API:', response.models.map(m => m.id));
          console.log('[ModelStore] Loaded providers:', response.providers.map(p => p.id));
          
          // Get saved provider and model from store or use defaults
          const currentProvider = get().selectedProvider;
          const currentModel = get().selectedModel;
          
          console.log('[ModelStore] Current provider:', currentProvider);
          console.log('[ModelStore] Current model:', currentModel);
          console.log('[ModelStore] Default provider from API:', response.default_provider);
          console.log('[ModelStore] Default model from API:', response.default_model);
          
          let finalProvider = currentProvider || response.default_provider;
          let finalModel = currentModel || response.default_model;
          
          // Validate provider exists and is available
          const providerExists = response.providers.find(
            p => p.id === finalProvider && p.available
          );
          
          if (!providerExists) {
            // Fall back to first available provider
            const firstProvider = response.providers.find(p => p.available);
            finalProvider = firstProvider?.id || response.default_provider;
            console.log('[ModelStore] Falling back to first available provider:', finalProvider);
          }
          
          // Validate model exists and belongs to selected provider
          const modelExists = response.models.find(
            m => m.id === finalModel && 
                 m.provider === finalProvider && 
                 m.available
          );
          
          if (!modelExists) {
            // Fall back to first model of selected provider
            const providerModels = response.models.filter(
              m => m.provider === finalProvider && m.available
            );
            finalModel = providerModels[0]?.id || response.default_model;
            console.log('[ModelStore] Falling back to first model of provider:', finalModel);
          }
          
          set({
            availableProviders: response.providers,
            availableModels: response.models,
            selectedProvider: finalProvider,
            selectedModel: finalModel,
            loading: false,
          });
          
          console.log('[ModelStore] Loaded providers:', response.providers.length);
          console.log('[ModelStore] Loaded models:', response.models.length);
          console.log('[ModelStore] Selected provider:', finalProvider);
          console.log('[ModelStore] Selected model:', finalModel);
        } catch (err) {
          console.error('[ModelStore] Failed to load models:', err);
          set({
            error: err instanceof Error ? err.message : 'Failed to load models',
            loading: false,
          });
        }
      },
      
      getSelectedModelInfo: () => {
        const { selectedModel, availableModels } = get();
        if (!selectedModel) return null;
        return availableModels.find(m => m.id === selectedModel) || null;
      },
      
      reset: () => {
        set({
          selectedProvider: null,
          selectedModel: null,
          availableProviders: [],
          availableModels: [],
          loading: false,
          error: null,
        });
      },
    }),
    {
      name: MODEL_STORAGE_KEY,
      storage: createJSONStorage(() => localStorage),
      // Persist both provider and model
      partialize: (state) => ({ 
        selectedProvider: state.selectedProvider,
        selectedModel: state.selectedModel 
      }),
    }
  )
);

// Auto-load models on first access
let hasInitialized = false;
export const initializeModelStore = () => {
  if (hasInitialized) return;
  hasInitialized = true;
  useModelStore.getState().loadModels();
};
