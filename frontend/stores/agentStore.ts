/**
 * Agent Store - Zustand
 * 
 * Global store for managing agent selection state
 * Uses Zustand with persist middleware for localStorage sync
 */

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { AgentMetadata } from '@/types/agent';
import { fetchAvailableAgents } from '@/services/api';

const AGENT_STORAGE_KEY = 'selected_agent';

interface AgentStore {
  // State
  selectedAgent: string;
  availableAgents: AgentMetadata[];
  loading: boolean;
  error: string | null;
  
  // Actions
  setSelectedAgent: (agentId: string) => void;
  loadAgents: () => Promise<void>;
  reset: () => void;
}

export const useAgentStore = create<AgentStore>()(
  persist(
    (set, get) => ({
      // Initial state
      selectedAgent: '',
      availableAgents: [],
      loading: false,
      error: null,
      
      // Actions
      setSelectedAgent: (agentId: string) => {
        console.log('[AgentStore] Setting agent to:', agentId);
        set({ selectedAgent: agentId });
      },
      
      loadAgents: async () => {
        const { loading } = get();
        if (loading) return; // Prevent duplicate loads
        
        try {
          set({ loading: true, error: null });
          console.log('[AgentStore] Loading agents...');
          
          const response = await fetchAvailableAgents();
          
          // Get saved agent from store or use default
          const currentAgent = get().selectedAgent;
          const agentToSelect = currentAgent && 
            response.agents.some(a => a.id === currentAgent)
              ? currentAgent
              : response.default;
          
          set({
            availableAgents: response.agents,
            selectedAgent: agentToSelect,
            loading: false,
          });
          
          console.log('[AgentStore] Loaded agents:', response.agents.length);
        } catch (err) {
          console.error('[AgentStore] Failed to load agents:', err);
          set({
            error: err instanceof Error ? err.message : 'Failed to load agents',
            loading: false,
          });
        }
      },
      
      reset: () => {
        set({
          selectedAgent: '',
          availableAgents: [],
          loading: false,
          error: null,
        });
      },
    }),
    {
      name: AGENT_STORAGE_KEY,
      storage: createJSONStorage(() => localStorage),
      // Only persist selectedAgent
      partialize: (state) => ({ selectedAgent: state.selectedAgent }),
    }
  )
);

// Auto-load agents on first access
let hasInitialized = false;
export const initializeAgentStore = () => {
  if (hasInitialized) return;
  hasInitialized = true;
  useAgentStore.getState().loadAgents();
};
