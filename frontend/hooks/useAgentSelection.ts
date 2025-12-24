import { useState, useEffect } from 'react';
import { AgentMetadata } from '@/types/agent';
import { fetchAvailableAgents } from '@/services/api';

const AGENT_STORAGE_KEY = 'selected_agent';

/**
 * Hook for managing agent selection
 * 
 * Fetches available agents from backend and manages selection state
 * Persists selection to localStorage
 */
export function useAgentSelection() {
  const [selectedAgent, setSelectedAgentState] = useState<string>('');
  const [availableAgents, setAvailableAgents] = useState<AgentMetadata[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Fetch available agents on mount
  useEffect(() => {
    const loadAgents = async () => {
      try {
        setLoading(true);
        const response = await fetchAvailableAgents();
        setAvailableAgents(response.agents);
        
        // Load saved selection or use default
        const saved = localStorage.getItem(AGENT_STORAGE_KEY);
        const initial = saved || response.default;
        
        // Validate saved agent is still available
        const isValid = response.agents.some(a => a.id === initial);
        setSelectedAgentState(isValid ? initial : response.default);
        
        setError(null);
      } catch (err) {
        console.error('Failed to load agents:', err);
        setError('Failed to load agents');
        
        // Keep empty state - UI should handle error/loading state
        setAvailableAgents([]);
        setSelectedAgentState('');
      } finally {
        setLoading(false);
      }
    };
    
    loadAgents();
  }, []);
  
  // Persist selection to localStorage
  const setSelectedAgent = (agentId: string) => {
    setSelectedAgentState(agentId);
    localStorage.setItem(AGENT_STORAGE_KEY, agentId);
  };
  
  return {
    selectedAgent,
    availableAgents,
    setSelectedAgent,
    loading,
    error
  };
}
