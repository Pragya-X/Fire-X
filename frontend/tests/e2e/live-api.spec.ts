/** Real HTTP backend, disposable SQLite and published NASA tutorial observations. */
import { test, expect } from "@playwright/test";

test("imports observations through the real pipeline and saves a draft through the browser", async ({ page, request }) => {
  const login = await request.post("http://127.0.0.1:8101/api/v1/auth/login", { data: { email: "e2e@example.invalid", password: "isolated-e2e-password" } });
  expect(login.ok()).toBeTruthy(); const token = (await login.json()).access_token;
  await page.addInitScript(value => localStorage.setItem("firex_token",value),token);
  await page.route(/basemaps|arcgisonline|demotiles/, route => route.abort());
  // The production bundle's API origin is rewritten to the disposable server.
  // All API requests execute the real FastAPI handlers and SQLite transactions.
  await page.route("**/api/v1/**", async route => {
    if (route.request().url().includes("/events/stream")) return route.abort();
    const url = new URL(route.request().url()); url.hostname = "127.0.0.1"; url.port = "8101";
    const response = await route.fetch({ url: url.toString() }); await route.fulfill({ response });
  });
  await page.goto("/event-workspace");
  await expect(page.getByText(/3 loaded of 3 matching events/)).toBeVisible();
  await page.getByRole("button", { name: /^EV-/ }).first().click();
  await expect(page.getByText(/Annotation · revision 0/)).toBeVisible();
  await page.getByLabel("Notes", { exact: true }).fill("Isolated browser test draft; no scientific label assigned.");
  await page.getByRole("button", { name: "Save draft" }).click();
  await expect(page.getByText(/Annotation · revision 1 · draft/)).toBeVisible();
  const exported = await request.get("http://127.0.0.1:8101/api/v1/thermal-events/annotations/export", { headers: { Authorization: `Bearer ${token}` } });
  const labels = await exported.json(); expect(labels).toHaveLength(1); expect(labels[0].label).toBe("Unknown");
  expect(labels[0].review_status).toBe("draft");
  await page.screenshot({ path: "test-results/event-workspace.png", fullPage: true });
});
