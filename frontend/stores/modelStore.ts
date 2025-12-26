/**
 * Model Store - Zustand
 * 
 * Global store for managing LLM model selection state
 * Uses Zustand with persist middleware for localStorage sync
 */

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { LLMModel, ModelsResponse } from '@/types/chat';
import { fetchAvailableModels } from '@/services/api';

const MODEL_STORAGE_KEY = 'selected-llm-model';

interface ModelStore {
  // State
  selectedModel: string | null;
  availableModels: LLMModel[];
  loading: boolean;
  error: string | null;
  
  // Actions
  setSelectedModel: (modelId: string) => void;
  loadModels: () => Promise<void>;
  getSelectedModelInfo: () => LLMModel | null;
  reset: () => void;
}

export const useModelStore = create<ModelStore>()(
  persist(
    (set, get) => ({
      // Initial state
      selectedModel: null,
      availableModels: [],
      loading: false,
      error: null,
      
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
          
          // Get saved model from store or use default
          const currentModel = get().selectedModel;
          console.log('[ModelStore] Current model:', currentModel);
          console.log('[ModelStore] Default model from API:', response.default);
          
          const modelToSelect = currentModel || response.default;
          
          // Verify the model exists and is available
          const modelExists = response.models.find(
            m => m.id === modelToSelect && m.available
          );
          
          let finalModel: string;
          if (modelExists) {
            console.log('[ModelStore] Using model:', modelToSelect);
            finalModel = modelToSelect;
          } else {
            // Fall back to first available model
            const firstAvailable = response.models.find(m => m.available);
            if (firstAvailable) {
              console.log('[ModelStore] Falling back to first available:', firstAvailable.id);
              finalModel = firstAvailable.id;
            } else {
              console.error('[ModelStore] No available models found');
              finalModel = response.default;
            }
          }
          
          set({
            availableModels: response.models,
            selectedModel: finalModel,
            loading: false,
          });
          
          console.log('[ModelStore] Loaded models:', response.models.length);
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
          selectedModel: null,
          availableModels: [],
          loading: false,
          error: null,
        });
      },
    }),
    {
      name: MODEL_STORAGE_KEY,
      storage: createJSONStorage(() => localStorage),
      // Only persist selectedModel
      partialize: (state) => ({ selectedModel: state.selectedModel }),
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
