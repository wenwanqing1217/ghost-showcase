import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    include: ['src/**/*.test.ts', 'src/**/*.test.tsx'],
    environment: 'node',
    coverage: {
      reporter: ['text', 'json'],
    },
  },
  resolve: {
    alias: {
      '@': './src',
    },
  },
});
