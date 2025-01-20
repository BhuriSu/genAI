import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        // if your backend doesn't have /api prefix, add:
        // rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  }
})