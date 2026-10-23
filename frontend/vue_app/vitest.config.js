// Configuración de las pruebas unitarias del frontend (Vitest). Ejecutar con: npm test
import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  test: {
    environment: 'jsdom',          // DOM simulado para montar componentes Vue
    include: ['tests/**/*.test.js'],
  },
})
