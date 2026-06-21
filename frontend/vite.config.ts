import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Test config (jsdom) lives here so `npx vitest run` works without extra flags.
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/tests/setup.ts'],
    globals: true,
  },
})
