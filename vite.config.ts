/// <reference types="vitest" />
import { defineConfig } from 'vitest/config';
import vue from '@vitejs/plugin-vue';

export default defineConfig({
  plugins: [vue()],
  server: {
    host: "127.0.0.1",
    strictPort: true,
    proxy: {
      '/api': {
        target: process.env.FITADAPT_API_TARGET || 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
  test: {
    dir: './tests',
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./tests/setup.ts'],
    coverage: {
      provider: 'v8',
      include: ['src/**/*.vue', 'src/**/*.ts'],
      exclude: ['src/main.ts', 'src/env.d.ts', 'src/types/**'],
      reporter: ['text', 'html', 'lcov'],
      reportsDirectory: './coverage/vue',
      thresholds: { lines: 90, statements: 90, functions: 90, branches: 85 },
    },
  },
});
