import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./tests/e2e", timeout: 30000, fullyParallel: false, workers: 1,
  reporter: [["list"], ["json", { outputFile: "test-results/results.json" }]],
  use: { baseURL: process.env.E2E_BASE_URL || "http://127.0.0.1:3101", browserName: "chromium", headless: true, trace: "retain-on-failure" },
  webServer: [{ command: "npm run start", url: "http://127.0.0.1:3101/login", reuseExistingServer: false,
    env: { PORT: "3101", HOSTNAME: "127.0.0.1" }, timeout: 60000 },
    { command: "../.venv/bin/python ../backend/tests/e2e_server.py", url: "http://127.0.0.1:8101/api/v1/health",
      env: { PYTHONPATH: "../backend" }, reuseExistingServer: false, timeout: 60000 }],
});
