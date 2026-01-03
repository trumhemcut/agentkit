/**
 * Tests for A2UIManager
 */

import { A2UIManager } from '@/lib/a2ui/A2UIManager';
import { useA2UIStore } from '@/stores/a2uiStore';
import type { UserAction } from '@/types/a2ui';

// Mock the store
jest.mock('@/stores/a2uiStore');

describe('A2UIManager', () => {
  let manager: A2UIManager;
  let mockGetState: jest.Mock;

  beforeEach(() => {
    manager = new A2UIManager();
    
    // Setup mock store
    mockGetState = jest.fn();
    (useA2UIStore.getState as jest.Mock) = mockGetState;
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('onAction', () => {
    it('should register action callback', () => {
      const callback = jest.fn();
      manager.onAction('test-surface', callback);
      
      // Trigger action
      manager.handleComponentAction('test-surface', 'btn-1', 'test_action', {});
      
      expect(callback).toHaveBeenCalledWith(
        expect.objectContaining({
          name: 'test_action',
          surfaceId: 'test-surface',
          sourceComponentId: 'btn-1'
        })
      );
    });

    it('should support wildcard surface registration', () => {
      const callback = jest.fn();
      manager.onAction('*', callback);
      
      // Trigger action on any surface
      manager.handleComponentAction('any-surface', 'btn-1', 'test_action', {});
      
      expect(callback).toHaveBeenCalled();
    });

    it('should prefer specific surface callback over wildcard', () => {
      const wildcardCallback = jest.fn();
      const specificCallback = jest.fn();
      
      manager.onAction('*', wildcardCallback);
      manager.onAction('specific-surface', specificCallback);
      
      manager.handleComponentAction('specific-surface', 'btn-1', 'test', {});
      
      expect(specificCallback).toHaveBeenCalled();
      expect(wildcardCallback).not.toHaveBeenCalled();
    });
  });

  describe('handleComponentAction', () => {
    it('should create UserAction with correct structure', () => {
      const callback = jest.fn();
      manager.onAction('test-surface', callback);
      
      mockGetState.mockReturnValue({
        getValueAtPath: jest.fn().mockReturnValue(undefined)
      });
      
      manager.handleComponentAction(
        'test-surface',
        'component-1',
        'my_action',
        { field: 'value' }
      );
      
      const userAction: UserAction = callback.mock.calls[0][0];
      
      expect(userAction).toMatchObject({
        name: 'my_action',
        surfaceId: 'test-surface',
        sourceComponentId: 'component-1',
        context: { field: 'value' }
      });
      expect(userAction.timestamp).toMatch(/^\d{4}-\d{2}-\d{2}T/);
    });

    it('should warn if no callback is registered', () => {
      const consoleSpy = jest.spyOn(console, 'warn').mockImplementation();
      
      mockGetState.mockReturnValue({
        getValueAtPath: jest.fn()
      });
      
      manager.handleComponentAction('unknown', 'btn-1', 'action', {});
      
      expect(consoleSpy).toHaveBeenCalledWith(
        expect.stringContaining('No action callback registered')
      );
      
      consoleSpy.mockRestore();
    });
  });

  describe('resolveActionContext', () => {
    beforeEach(() => {
      mockGetState.mockReturnValue({
        getValueAtPath: jest.fn((surfaceId: string, path: string) => {
          const mockData: Record<string, any> = {
            '/user/email': 'user@example.com',
            '/user/name': 'John Doe',
            '/form/age': 25
          };
          return mockData[path];
        })
      });
    });

    it('should resolve path references to actual values', () => {
      const context = {
        email: { path: '/user/email' },
        name: { path: '/user/name' }
      };
      
      const resolved = manager.resolveActionContext('test-surface', context);
      
      expect(resolved).toEqual({
        email: 'user@example.com',
        name: 'John Doe'
      });
    });

    it('should keep literal values unchanged', () => {
      const context = {
        literalString: 'hello',
        literalNumber: 42,
        literalBoolean: true,
        literalObject: { nested: 'value' }
      };
      
      const resolved = manager.resolveActionContext('test-surface', context);
      
      expect(resolved).toEqual(context);
    });

    it('should handle mixed context with paths and literals', () => {
      const context = {
        email: { path: '/user/email' },
        formType: 'contact',
        age: { path: '/form/age' },
        timestamp: new Date().toISOString()
      };
      
      const resolved = manager.resolveActionContext('test-surface', context);
      
      expect(resolved).toEqual({
        email: 'user@example.com',
        formType: 'contact',
        age: 25,
        timestamp: expect.any(String)
      });
    });

    it('should handle undefined path values', () => {
      mockGetState.mockReturnValue({
        getValueAtPath: jest.fn().mockReturnValue(undefined)
      });
      
      const context = {
        missing: { path: '/nonexistent/path' }
      };
      
      const resolved = manager.resolveActionContext('test-surface', context);
      
      expect(resolved).toEqual({
        missing: undefined
      });
    });

    it('should handle empty context', () => {
      const resolved = manager.resolveActionContext('test-surface', {});
      expect(resolved).toEqual({});
    });
  });

  describe('updateDataModelValue', () => {
    it('should call store setValueAtPath', () => {
      const mockSetValueAtPath = jest.fn();
      mockGetState.mockReturnValue({
        setValueAtPath: mockSetValueAtPath
      });
      
      manager.updateDataModelValue('test-surface', '/user/email', 'new@email.com');
      
      expect(mockSetValueAtPath).toHaveBeenCalledWith(
        'test-surface',
        '/user/email',
        'new@email.com'
      );
    });
  });

  describe('getValueAtPath', () => {
    it('should call store getValueAtPath', () => {
      const mockGetValueAtPath = jest.fn().mockReturnValue('test-value');
      mockGetState.mockReturnValue({
        getValueAtPath: mockGetValueAtPath
      });
      
      const value = manager.getValueAtPath('test-surface', '/user/email');
      
      expect(mockGetValueAtPath).toHaveBeenCalledWith('test-surface', '/user/email');
      expect(value).toBe('test-value');
    });
  });
});
