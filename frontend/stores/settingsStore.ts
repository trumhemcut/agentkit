/**
 * Settings Store - Zustand
 * 
 * Global store for managing agent settings state
 */

import { create } from 'zustand';
import { AgentSettings } from '@/types/settings';
import { 
  getMockAgentSettings, 
  updateMockAgentSettings 
} from '@/services/settings-mock';
import { toast } from 'sonner';

interface SettingsStore {
  // State
  agents: AgentSettings[];
  loading: boolean;
  error: string | null;
  selectedAgentId: string | null;
  
  // Actions
  loadAgents: () => Promise<void>;
  updateAgent: (id: string, updates: Partial<AgentSettings>) => Promise<void>;
  setSelectedAgent: (id: string | null) => void;
  reset: () => void;
}

export const useSettingsStore = create<SettingsStore>((set, get) => ({
  // Initial state
  agents: [],
  loading: false,
  error: null,
  selectedAgentId: null,
  
  // Actions
  loadAgents: async () => {
    const { loading } = get();
    if (loading) return; // Prevent duplicate loads
    
    try {
      set({ loading: true, error: null });
      console.log('[SettingsStore] Loading agent settings...');
      
      const agents = await getMockAgentSettings();
      
      set({
        agents,
        loading: false,
      });
      
      console.log('[SettingsStore] Loaded agent settings:', agents.length);
    } catch (err) {
      console.error('[SettingsStore] Failed to load agent settings:', err);
      const errorMessage = err instanceof Error ? err.message : 'Failed to load agent settings';
      set({
        error: errorMessage,
        loading: false,
      });
      toast.error(errorMessage);
    }
  },
  
  updateAgent: async (id: string, updates: Partial<AgentSettings>) => {
    try {
      console.log('[SettingsStore] Updating agent:', id, updates);
      
      // Optimistic update
      const { agents } = get();
      const optimisticAgents = agents.map(agent =>
        agent.id === id
          ? { ...agent, ...updates, updatedAt: new Date().toISOString() }
          : agent
      );
      set({ agents: optimisticAgents });
      
      // API call (mock)
      const updatedAgent = await updateMockAgentSettings(id, updates);
      
      // Update with server response
      const finalAgents = agents.map(agent =>
        agent.id === id ? updatedAgent : agent
      );
      set({ agents: finalAgents });
      
      toast.success('Agent settings updated successfully');
      console.log('[SettingsStore] Agent updated successfully:', updatedAgent);
    } catch (err) {
      console.error('[SettingsStore] Failed to update agent:', err);
      const errorMessage = err instanceof Error ? err.message : 'Failed to update agent settings';
      
      // Revert optimistic update
      await get().loadAgents();
      
      set({ error: errorMessage });
      toast.error(errorMessage);
    }
  },
  
  setSelectedAgent: (id: string | null) => {
    console.log('[SettingsStore] Setting selected agent to:', id);
    set({ selectedAgentId: id });
  },
  
  reset: () => {
    set({
      agents: [],
      loading: false,
      error: null,
      selectedAgentId: null,
    });
  },
}));

// Auto-load settings on first access (client-side only)
let hasInitialized = false;
export const initializeSettingsStore = () => {
  // Only run on client-side
  if (typeof window === 'undefined') return;
  if (hasInitialized) return;
  
  hasInitialized = true;
  
  // Small delay to ensure component is mounted
  setTimeout(() => {
    useSettingsStore.getState().loadAgents();
  }, 0);
};
