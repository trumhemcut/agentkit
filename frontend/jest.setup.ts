import '@testing-library/jest-dom'

// Mock ResizeObserver for Recharts
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
};

// Mock performance.getEntriesByType for performance tracking
if (!global.performance.getEntriesByType) {
  global.performance.getEntriesByType = jest.fn(() => []);
}

// Mock react-markdown to avoid ESM issues
jest.mock('react-markdown', () => ({
  __esModule: true,
  default: jest.fn(({ children }) => children),
}));

jest.mock('remark-gfm', () => ({
  __esModule: true,
  default: jest.fn(),
}));

jest.mock('rehype-highlight', () => ({
  __esModule: true,
  default: jest.fn(),
}));
