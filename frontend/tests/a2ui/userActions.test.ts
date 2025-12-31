/**
 * Unit tests for A2UI User Actions
 * 
 * Tests the A2UIManager action handling, context resolution, and integration
 * with the A2UI protocol for bidirectional communication.
 */

import { a2uiManager } from '@/lib/a2ui/A2UIManager';
import { useA2UIStore } from '@/stores/a2uiStore';
import { A2UIUserActionService } from '@/services/a2uiActionService';
import type { UserAction } from '@/types/a2ui';

describe('A2UI User Actions', () => {
  beforeEach(() => {
    // Reset store before each test
    const store = useA2UIStore.getState();
    store.surfaces.clear();
  });

  describe('A2UIManager Context Resolution', () => {
    it('should resolve action context paths from data model', () => {
      const store = useA2UIStore.getState();
      
      // Create a surface with data model
      store.createOrUpdateSurface('test_surface', []);
      store.updateDataModel('test_surface', '/', [
        { key: 'user', valueMap: { email: 'test@example.com', name: 'Test User' } }
      ]);
      
      // Resolve context with paths
      const context = a2uiManager.resolveActionContext('test_surface', {
        email: { path: '/user/email' },
        name: { path: '/user/name' },
        literal: 'static_value'
      });
      
      expect(context).toEqual({
        email: 'test@example.com',
        name: 'Test User',
        literal: 'static_value'
      });
    });

    it('should handle missing paths gracefully', () => {
      const store = useA2UIStore.getState();
      store.createOrUpdateSurface('test_surface', []);
      
      const context = a2uiManager.resolveActionContext('test_surface', {
        missing: { path: '/does/not/exist' },
        literal: 'value'
      });
      
      expect(context).toEqual({
        missing: undefined,
        literal: 'value'
      });
    });

    it('should handle nested paths correctly', () => {
      const store = useA2UIStore.getState();
      store.createOrUpdateSurface('test_surface', []);
      store.updateDataModel('test_surface', '/', [
        { 
          key: 'form', 
          valueMap: { 
            user: { 
              profile: { 
                email: 'nested@example.com' 
              } 
            } 
          } 
        }
      ]);
      
      const context = a2uiManager.resolveActionContext('test_surface', {
        email: { path: '/form/user/profile/email' }
      });
      
      expect(context.email).toBe('nested@example.com');
    });
  });

  describe('A2UIManager Action Handling', () => {
    it('should trigger action callback when handleComponentAction is called', () => {
      const mockCallback = jest.fn();
      const store = useA2UIStore.getState();
      
      store.createOrUpdateSurface('test_surface', []);
      a2uiManager.onAction('test_surface', mockCallback);
      
      a2uiManager.handleComponentAction(
        'test_surface',
        'submit_button',
        'submit_form',
        { field: 'value' }
      );
      
      expect(mockCallback).toHaveBeenCalledWith(
        expect.objectContaining({
          name: 'submit_form',
          surfaceId: 'test_surface',
          sourceComponentId: 'submit_button',
          context: { field: 'value' },
          timestamp: expect.any(String)
        })
      );
    });

    it('should support wildcard action handlers', () => {
      const mockCallback = jest.fn();
      const store = useA2UIStore.getState();
      
      store.createOrUpdateSurface('surface_1', []);
      store.createOrUpdateSurface('surface_2', []);
      
      // Register wildcard handler
      a2uiManager.onAction('*', mockCallback);
      
      // Trigger actions on different surfaces
      a2uiManager.handleComponentAction('surface_1', 'btn1', 'action1', {});
      a2uiManager.handleComponentAction('surface_2', 'btn2', 'action2', {});
      
      expect(mockCallback).toHaveBeenCalledTimes(2);
    });
  });

  describe('A2UIUserActionService', () => {
    it('should create properly formatted UserAction objects', () => {
      const action = A2UIUserActionService.createUserAction(
        'submit_form',
        'test_surface',
        'submit_button',
        { email: 'test@example.com', name: 'Test User' }
      );
      
      expect(action).toMatchObject({
        name: 'submit_form',
        surfaceId: 'test_surface',
        sourceComponentId: 'submit_button',
        timestamp: expect.any(String),
        context: {
          email: 'test@example.com',
          name: 'Test User'
        }
      });
      
      // Validate ISO 8601 timestamp format
      expect(() => new Date(action.timestamp)).not.toThrow();
    });
  });

  describe('Data Model Two-Way Binding', () => {
    it('should update data model values at path', () => {
      const store = useA2UIStore.getState();
      store.createOrUpdateSurface('test_surface', []);
      store.updateDataModel('test_surface', '/', [
        { key: 'form', valueMap: { email: '' } }
      ]);
      
      // Update value using setValueAtPath (mimics input onChange)
      a2uiManager.updateDataModelValue('test_surface', '/form/email', 'new@example.com');
      
      // Verify value was updated
      const value = a2uiManager.getValueAtPath('test_surface', '/form/email');
      expect(value).toBe('new@example.com');
    });

    it('should create nested paths if they do not exist', () => {
      const store = useA2UIStore.getState();
      store.createOrUpdateSurface('test_surface', []);
      
      // Set value on a path that doesn't exist yet
      a2uiManager.updateDataModelValue('test_surface', '/new/nested/path', 'value');
      
      const value = a2uiManager.getValueAtPath('test_surface', '/new/nested/path');
      expect(value).toBe('value');
    });
  });
});
