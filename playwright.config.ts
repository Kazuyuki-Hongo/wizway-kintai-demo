import { defineConfig, devices } from '@playwright/test';
import * as dotenv from 'dotenv';

dotenv.config({ path: '.env' });

const baseURL = (
  process.env.PLAYWRIGHT_BASE_URL || 'http://127.0.0.1:5173'
).replace(/\/$/, '');

const startLocalServers = !process.env.PLAYWRIGHT_BASE_URL;

export default defineConfig({
  testDir: 'tests/e2e',
  workers: 1,
  retries: process.env.CI ? 1 : 0,
  reporter: [
    ['list'],
    ['junit', { outputFile: 'junit.xml' }],
    ['html', { outputFolder: 'playwright-report', open: 'never' }],
  ],
  use: {
    baseURL,
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  timeout: 60_000,
  expect: { timeout: 10_000 },
  projects: [
    {
      name: 'attendance',
      use: { ...devices['Desktop Chrome'] },
      testMatch: /attendance\.spec\.ts/,
    },
  ],
  webServer: startLocalServers
    ? [
        {
          command: 'python backend/local_server.py',
          url: 'http://127.0.0.1:8080/employees',
          reuseExistingServer: !process.env.CI,
          timeout: 120_000,
        },
        {
          command: 'npm run dev -- --host 127.0.0.1 --port 5173',
          cwd: 'frontend',
          url: 'http://127.0.0.1:5173',
          reuseExistingServer: !process.env.CI,
          timeout: 120_000,
          env: {
            ...process.env,
            VITE_API_URL: 'http://127.0.0.1:8080',
          },
        },
      ]
    : undefined,
});
