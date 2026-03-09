import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const proxyTarget = process.env.VITE_PROXY_TARGET || 'http://localhost:9527'

export default defineConfig({
  plugins: [react()],
  resolve: {
    dedupe: ['react', 'react-dom'],
  },
  optimizeDeps: {
    include: ['react', 'react-dom', 'i18next', 'react-i18next'],
  },
  server: {
    port: 3847,
    host: true,
    allowedHosts: true,
    proxy: {
      '/api/v1': {
        target: proxyTarget,
        changeOrigin: true,
      }
    }
  }
})
