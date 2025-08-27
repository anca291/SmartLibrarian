import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // trimite toate cererile /audio/* la backend-ul FastAPI
      "/audio": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
      // dacă ai și /chat pe backend, merită proxiat și acesta:
      "/chat": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});