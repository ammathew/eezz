import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  preview: {
    host: '0.0.0.0',
    port: 3000,
    strictPort: true,
    allowedHosts: [
      'unravel.sunship.space',
      'app.unrav.me',
      'unravel.so',
      'app.unravel.so',
      'localhost',
      '127.0.0.1',
      '.sunship.space',
      '8077ddee1e26.ngrok-free.app'
    ]
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    allowedHosts: [
      'unravel.sunship.space',
      'app.unrav.me',
      'unravel.so',
      'app.unravel.so',
      'localhost',
      '127.0.0.1',
      '.sunship.space',
      '8077ddee1e26.ngrok-free.app',
      'local.eezz.test'
    ],
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/emails': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/backend-admin': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    }
  }
})
