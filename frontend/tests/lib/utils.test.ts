/**
 * Tests for utility functions
 */

import { generateUniqueId } from '@/lib/utils';

describe('generateUniqueId', () => {
  it('should generate unique IDs with prefix', () => {
    const id1 = generateUniqueId('test');
    const id2 = generateUniqueId('test');
    
    expect(id1).toMatch(/^test-\d+-\d+-[a-z0-9]+$/);
    expect(id2).toMatch(/^test-\d+-\d+-[a-z0-9]+$/);
    expect(id1).not.toBe(id2);
  });

  it('should generate unique IDs when called multiple times rapidly', () => {
    const ids = new Set<string>();
    const count = 1000;
    
    // Generate many IDs in rapid succession
    for (let i = 0; i < count; i++) {
      ids.add(generateUniqueId('msg'));
    }
    
    // All IDs should be unique
    expect(ids.size).toBe(count);
  });

  it('should use default prefix when not provided', () => {
    const id = generateUniqueId();
    expect(id).toMatch(/^id-\d+-\d+-[a-z0-9]+$/);
  });

  it('should maintain uniqueness across different prefixes', () => {
    const id1 = generateUniqueId('user');
    const id2 = generateUniqueId('agent');
    
    expect(id1).toMatch(/^user-/);
    expect(id2).toMatch(/^agent-/);
    expect(id1).not.toBe(id2);
  });

  it('should include timestamp, counter, and random components', () => {
    const id = generateUniqueId('test');
    const parts = id.split('-');
    
    expect(parts.length).toBe(4); // prefix-timestamp-counter-random
    expect(parts[0]).toBe('test'); // prefix
    expect(parseInt(parts[1])).toBeGreaterThan(0); // timestamp
    expect(parseInt(parts[2])).toBeGreaterThanOrEqual(0); // counter
    expect(parts[3].length).toBeGreaterThan(0); // random string
  });
});
