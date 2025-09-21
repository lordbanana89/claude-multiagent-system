import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8888',  // Main API Gateway (FastAPI)
        changeOrigin: true,
        secure: false,
      },
      '/auth': {
        target: 'http://localhost:5002',  // Auth API
        changeOrigin: true,
        secure: false,
      },
      '/health': {
        target: 'http://localhost:5001',  // Health API
        changeOrigin: true,
        secure: false,
      },
      '/ws': {
        target: 'ws://localhost:8888',    // WebSocket on main API
        ws: true,
        changeOrigin: true,
      },
    },
  },
})
