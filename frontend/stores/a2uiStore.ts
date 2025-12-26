import { create } from 'zustand';
import type { A2UIComponent } from '@/types/a2ui';

interface Surface {
  id: string;
  components: Map<string, A2UIComponent>; // Adjacency list
  dataModel: Record<string, any>;
  rootComponentId?: string;
  isRendering: boolean;
  messageId?: string; // Associate surface with a message
}

interface A2UIStore {
  surfaces: Map<string, Surface>;
  
  // Actions
  createOrUpdateSurface: (surfaceId: string, components: A2UIComponent[], messageId?: string) => void;
  updateDataModel: (surfaceId: string, path: string | undefined, contents: any[]) => void;
  beginRendering: (surfaceId: string, rootComponentId: string) => void;
  deleteSurface: (surfaceId: string) => void;
  getSurface: (surfaceId: string) => Surface | undefined;
  getSurfacesByMessageId: (messageId: string) => Surface[];
}

export const useA2UIStore = create<A2UIStore>((set, get) => ({
  surfaces: new Map(),
  
  createOrUpdateSurface: (surfaceId, components, messageId) => {
    set((state) => {
      const surfaces = new Map(state.surfaces);
      const existing = surfaces.get(surfaceId) || {
        id: surfaceId,
        components: new Map(),
        dataModel: {},
        isRendering: false,
        messageId
      };
      
      // Update messageId if provided
      if (messageId && !existing.messageId) {
        existing.messageId = messageId;
      }
      
      // Add/update components in adjacency list
      components.forEach((comp) => {
        existing.components.set(comp.id, comp);
      });
      
      surfaces.set(surfaceId, existing);
      return { surfaces };
    });
  },
  
  updateDataModel: (surfaceId, path, contents) => {
    set((state) => {
      const surfaces = new Map(state.surfaces);
      const surface = surfaces.get(surfaceId);
      
      if (!surface) return state;
      
      // Update data model at path
      if (!path || path === '/') {
        // Replace entire model
        const newModel: Record<string, any> = {};
        contents.forEach(({ key, valueString, valueNumber, valueBoolean, valueMap }) => {
          newModel[key] = valueString ?? valueNumber ?? valueBoolean ?? valueMap;
        });
        surface.dataModel = newModel;
      } else {
        // Update at specific path (simplified JSON Pointer)
        const keys = path.split('/').filter(k => k);
        let current = surface.dataModel;
        
        // Navigate to parent
        for (let i = 0; i < keys.length - 1; i++) {
          if (!current[keys[i]]) current[keys[i]] = {};
          current = current[keys[i]];
        }
        
        // Set value
        const lastKey = keys[keys.length - 1];
        if (!current[lastKey]) current[lastKey] = {};
        
        contents.forEach(({ key, valueString, valueNumber, valueBoolean, valueMap }) => {
          current[lastKey][key] = valueString ?? valueNumber ?? valueBoolean ?? valueMap;
        });
      }
      
      surfaces.set(surfaceId, surface);
      return { surfaces };
    });
  },
  
  beginRendering: (surfaceId, rootComponentId) => {
    set((state) => {
      const surfaces = new Map(state.surfaces);
      const surface = surfaces.get(surfaceId);
      
      if (!surface) return state;
      
      surface.rootComponentId = rootComponentId;
      surface.isRendering = true;
      surfaces.set(surfaceId, surface);
      
      return { surfaces };
    });
  },
  
  deleteSurface: (surfaceId) => {
    set((state) => {
      const surfaces = new Map(state.surfaces);
      surfaces.delete(surfaceId);
      return { surfaces };
    });
  },
  
  getSurface: (surfaceId) => {
    return get().surfaces.get(surfaceId);
  },
  
  getSurfacesByMessageId: (messageId) => {
    const surfaces = Array.from(get().surfaces.values());
    return surfaces.filter(surface => surface.messageId === messageId);
  }
}));
