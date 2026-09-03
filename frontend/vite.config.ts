import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // 本地开发后端跑在 8010（8000 被其他项目占用）
      '/api': 'http://localhost:8010',
    },
  },
})
