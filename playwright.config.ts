import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: 2,
  timeout: 30_000,
  expect: { timeout: 7_000 },
  reporter: [['list'], ['html', { open: 'never' }]],
  use: {
    baseURL: 'http://127.0.0.1:4179',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    { name: 'chrome', use: { ...devices['Desktop Chrome'], channel: 'chrome' } },
    { name: 'mobile-chrome', use: { ...devices['Pixel 7'], channel: 'chrome' } },
  ],
  webServer: [
    {
      command: 'node scripts/python.mjs -m uvicorn e2e.api_test_app:app --host 127.0.0.1 --port 8019',
      url: 'http://127.0.0.1:8019/api/health',
      reuseExistingServer: false,
      env: { FITADAPT_MODE: 'demo', OPENAI_API_KEY: '', OPENAI_BASE_URL: 'http://127.0.0.1:9', PYTHON_DOTENV_DISABLED: '1' },
      timeout: 30_000,
    },
    {
      command: 'npm run build && npm run preview -- --host 127.0.0.1 --port 4179 --strictPort',
      url: 'http://127.0.0.1:4179',
      reuseExistingServer: false,
      env: {
        FITADAPT_API_TARGET: 'http://127.0.0.1:8019',
        VITE_CLERK_PUBLISHABLE_KEY: '',
        VITE_E2E_AUTH: 'true',
      },
      timeout: 90_000,
    },
  ],
});
