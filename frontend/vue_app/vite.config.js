import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/api': {
        //target: 'http://django_backend:8000',
        target: 'http://data4cdpv1-backend-1:8000',
        changeOrigin: false,
        secure: false
      }

    }
  }
})
