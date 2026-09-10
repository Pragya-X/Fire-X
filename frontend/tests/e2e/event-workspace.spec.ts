/** Contract/UI tests. Intercepted payloads are unit fixtures, not scientific evidence. */
import { test, expect } from "@playwright/test";
const user = { id: 1, name: "Unit Analyst", email: "unit@example.invalid", role: "analyst", is_active: true, created_at: "2025-01-01" };
const event = {
  event_id: "UNIT-ONLY", latitude: 22, longitude: 78, start_time: "2025-01-01T00:00:00Z", end_time: "2025-01-01T00:05:00Z", facility_id: null,
  features: { mean_frp: 10, detection_count: 1, active_days_90d: null, dist_nearest_industrial_km: null }, provenance: { data_type: "unit_test_only" },
  intelligence: { decision: "Unknown", confidence: null, confidence_type: "unavailable", mode: "evidence_rules", reasons: ["No approved event classifier"],
    anomaly: { status: "unavailable", score: null, historical_mean_mw: null, reason: "No history" },
    persistence: { status: "insufficient_history", observed_recurrence: null, reason: "No history" }, explanation: { shap: { available: false, reason: "No approved event model loaded" } } },
};

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => localStorage.setItem("firex_token","unit-token"));
  // Avoid external tiles in contract tests. Map/browser integration is independent of tile availability.
  await page.route(/basemaps|arcgisonline|demotiles/, route => route.abort());
  await page.route("**/api/v1/**", async route => {
    const path = new URL(route.request().url()).pathname;
    if (path.endsWith("/auth/me")) return route.fulfill({ json: user });
    if (path.endsWith("/thermal-events/status")) return route.fulfill({ json: { event_count: 1, model_mode: "evidence_rules", training_ready: false, reason: "No approved real event classifier", classes: ["Unknown","Industrial Fire"] } });
    if (path.endsWith("/thermal-events")) return route.fulfill({ json: { items: [event], total: 1 } });
    if (path.endsWith("/thermal-events/UNIT-ONLY")) return route.fulfill({ json: { ...event, observations: [{ acquisition_time: event.start_time, frp: 10 }], annotations: [] } });
    if (path.endsWith("/alerts/notifications")) return route.fulfill({ json: { items: [], unread: 0 } });
    return route.fulfill({ status: 503, json: { detail: "Unit test: unrelated endpoint unavailable" } });
  });
});

test("shows missing confidence and SHAP and submits an honest draft", async ({ page }) => {
  const errors: string[] = []; page.on("pageerror", e => errors.push(e.message));
  await page.goto("/event-workspace");
  await expect(page.getByText("Model: evidence_rules · Training: Blocked")).toBeVisible();
  await page.getByRole("button", { name: "UNIT-ONLY", exact: true }).click();
  await expect(page.getByText("SHAP: No approved event model loaded")).toBeVisible();
  await expect(page.getByText("Unknown · Confidence: Unavailable (unavailable)")).toBeVisible();
  await expect(page.getByRole("button", { name: "Approve submitted revision" })).toBeDisabled();
  let captured: Record<string,unknown> | undefined;
  await page.route("**/thermal-events/UNIT-ONLY/annotations", async route => {
    captured = route.request().postDataJSON();
    await route.fulfill({ json: { revision: 1, training_eligible: false } });
  });
  await page.getByRole("button", { name: "Save draft" }).click();
  await expect(page.getByText("Annotation revision saved.")).toBeVisible();
  expect(captured).toMatchObject({ expected_revision: 0, action: "save", label: "Unknown", confidence: null, quality: "C", evidence: [] });
  expect(errors).toEqual([]);
});

test("shows an empty dataset without inserting demo observations", async ({ page }) => {
  await page.route("**/api/v1/thermal-events?**", route => route.fulfill({ json: { items: [], total: 0 } }));
  await page.goto("/event-workspace");
  await expect(page.getByText(/No observations imported for these filters/)).toBeVisible();
  await expect(page.getByRole("button", { name: "Play timeline" })).toBeDisabled();
});

test("surfaces API failure instead of claiming empty data", async ({ page }) => {
  await page.route("**/api/v1/thermal-events?**", route => route.fulfill({ status: 503, json: { detail: "Event store unavailable" } }));
  await page.goto("/event-workspace");
  await expect(page.getByRole("alert").filter({ hasText: "Event store unavailable" })).toBeVisible();
  await expect(page.getByText(/No observations imported for these filters/)).toHaveCount(0);
});

test("keeps core navigation and exposes working settings only", async ({ page }) => {
  await page.route("**/api/v1/system-health", route => route.fulfill({ json: {
    demo_mode: true, overall: "operational", components: [
      { name: "NASA FIRMS", mode: "DEMO", status: "operational", detail: "Demo provider" },
    ],
  } }));
  await page.goto("/settings");
  const navigation = page.getByRole("navigation", { name: "Main navigation" }).first();
  for (const name of ["Home", "Live Map", "Event Details", "Analytics", "AI Results", "Reports", "Settings"]) {
    await expect(navigation.getByRole("link", { name, exact: true })).toBeVisible();
  }
  await expect(page.getByText("Demo observations are not a training dataset.", { exact: false })).toBeVisible();
  await expect(page.getByRole("link", { name: "Edit profile or change password" })).toHaveAttribute("href", "/profile");
  await expect(page.getByRole("button", { name: "Refresh status" })).toBeEnabled();
  await expect(page.getByRole("button", { name: "Save settings" })).toHaveCount(0);
  await navigation.getByText("More tools", { exact: true }).click();
  await expect(navigation.getByRole("link", { name: "Data ingestion", exact: true })).toBeVisible();
});

for (const demoMode of [false, true]) {
  test(`demo controls follow backend mode (${demoMode})`, async ({ page }) => {
    await page.route("**/api/v1/system-health", route => route.fulfill({ json: {
      demo_mode: demoMode, overall: "operational", components: [],
    } }));
    await page.goto("/ingestion");
    await expect(page.getByRole("heading", { name: "Data Ingestion" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Sync FIRMS", exact: true })).toBeVisible();
    for (const name of ["Sync demo batch", "Preview demo land cover"]) {
      await expect(page.getByRole("button", { name, exact: true })).toHaveCount(demoMode ? 1 : 0);
    }
    await page.goto("/");
    await expect(page.getByRole("heading", { name: "Home", exact: true })).toBeVisible();
    await expect(page.getByRole("button", { name: "Run Demo Scenario", exact: true })).toHaveCount(demoMode ? 1 : 0);
  });
}
