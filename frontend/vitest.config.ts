import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// Config de test separada de vite.config.ts: los tests de hooks no
// necesitan (ni quieren) que vite-plugin-electron intente compilar
// electron/main.ts y electron/preload.ts en cada run.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  test: {
    environment: 'jsdom',
    globals: true,
  },
})
