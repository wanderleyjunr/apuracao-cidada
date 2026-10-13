import { defineConfig } from 'vite'
export default defineConfig({
  base: './',
  server: {
    fs: { allow: ['..'] }, // shared/ lives outside app/
    proxy: { '/api': 'http://localhost:8787' }, // server/confere/dev_server.py
  },
  test: { include: ['src/**/*.test.ts', '../shared/**/*.test.ts'] },
} as never)
