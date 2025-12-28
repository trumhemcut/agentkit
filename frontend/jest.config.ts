import type { Config } from 'jest'
import nextJest from 'next/jest'

const createJestConfig = nextJest({
  // Provide the path to your Next.js app to load next.config.js and .env files in your test environment
  dir: './',
})

// Add any custom config to be passed to Jest
const config: Config = {
  coverageProvider: 'v8',
  testEnvironment: 'jsdom',
  // Add more setup options before each test is run
  setupFilesAfterEnv: ['<rootDir>/jest.setup.ts'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/$1',
  },
  testMatch: [
    '<rootDir>/tests/**/*.test.{ts,tsx}',
    '<rootDir>/**/*.test.{ts,tsx}',
  ],
  transformIgnorePatterns: [
    'node_modules/(?!(react-markdown|remark-gfm|rehype-highlight|rehype-raw|remark-parse|remark-rehype|unified|bail|is-plain-obj|trough|vfile|vfile-message|unist-.*|hast-.*|mdast-.*|micromark.*|decode-named-character-reference|character-entities|property-information|space-separated-tokens|comma-separated-tokens|web-namespaces|zwitch|html-void-elements)/)',
  ],
}

// createJestConfig is exported this way to ensure that next/jest can load the Next.js config which is async
export default createJestConfig(config)
