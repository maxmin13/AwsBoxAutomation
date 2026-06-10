import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  root: 'src',
  build: {
    outDir: '../dist',
    emptyOutDir: true,
  },
  // Relative asset paths so Electron can load dist/index.html via file://
  base: './',
  server: {
    port: 5173,
  },
})
