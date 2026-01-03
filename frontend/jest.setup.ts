import '@testing-library/jest-dom'
import { TextEncoder, TextDecoder } from 'util';

// Polyfill TextEncoder and TextDecoder for Jest
global.TextEncoder = TextEncoder;
global.TextDecoder = TextDecoder as any;

// Mock ResizeObserver for Recharts
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
};

// Mock matchMedia for media query hooks
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // deprecated
    removeListener: jest.fn(), // deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

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
