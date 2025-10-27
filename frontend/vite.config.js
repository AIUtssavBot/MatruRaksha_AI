import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true,
    cors: true
  },
<<<<<<< HEAD
  // ADD THE PREVIEW CONFIGURATION BLOCK HERE
  preview: {
    // Allows the specified host to access the preview server
    allowedHosts: ['.hello-xo.nl']
  },
=======
>>>>>>> 6eb2a328ef725bea436f28cc077fc497fe3c112b
  build: {
    outDir: 'dist',
    sourcemap: false
  }
})