import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    minify: false,
    sourcemap: true
  },
  server: {
    port: 3000
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/setupTests.ts'],
    globals: true,
    env: {
      DEV: 'false',
      VITE_BACKEND_URL: 'http://localhost:3000'
    }
  }
})
