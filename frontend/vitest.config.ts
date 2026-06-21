import { defineConfig, mergeConfig } from 'vitest/config'
import viteConfig from './vite.config'

// Vitest configuration. Merges the canonical Vite config (so the React plugin
// and resolve settings stay in sync) and layers the test-only options on top.
export default mergeConfig(
  viteConfig,
  defineConfig({
    test: {
      environment: 'jsdom',
      setupFiles: ['./src/tests/setup.ts'],
      globals: true,
      include: ['src/**/*.{test,spec}.{ts,tsx}'],
    },
  }),
)
