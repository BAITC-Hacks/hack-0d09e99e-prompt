import { defineConfig } from "@playwright/test";

// e2e ходят в живую связку: Next на :3000 (поднимется сам, если не запущен)
// и FastAPI на :8000 (должен быть запущен заранее — там демо-данные и состояние заказа).
export default defineConfig({
  testDir: "./e2e",
  timeout: 45_000,
  workers: 1, // состояние заказа одно на всех — параллелить нельзя
  retries: 0,
  reporter: [["list"]],
  use: {
    // localhost, не 127.0.0.1: на IPv4 может висеть старый dev-сервер.
    baseURL: "http://localhost:3000",
    trace: "retain-on-failure",
  },
  projects: [{ name: "chromium", use: { browserName: "chromium" } }],
  webServer: {
    command: "npm run dev",
    url: "http://localhost:3000",
    reuseExistingServer: true,
    timeout: 120_000,
  },
});
