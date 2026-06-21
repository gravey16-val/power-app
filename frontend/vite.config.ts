import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Canonical Vite app config (dev server + build).
// Vitest test configuration lives in vitest.config.ts, which merges this file.
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
  },
})
