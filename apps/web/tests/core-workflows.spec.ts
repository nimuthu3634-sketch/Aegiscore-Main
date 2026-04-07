import { expect, test } from "@playwright/test";
import {
  apiPassword,
  apiUsername,
  attachAuthenticatedSession,
  clearStoredSession,
  expectPageHeading,
  seedThreatScenarios
} from "./support/e2e";

test.describe.configure({ mode: "serial", timeout: 120000 });

test.beforeAll(async ({ request }) => {
  await seedThreatScenarios(request);
});

test("login route authenticates and opens the overview dashboard", async ({
  page
}) => {
  await clearStoredSession(page);
  await page.goto("/login");

  await expectPageHeading(page, "Sign in to AegisCore");
  await expect(page.getByTestId("aegiscore-logo")).toHaveCount(1);
  await expect(page.getByTestId("aegiscore-logo").first()).toBeVisible();
  await page.getByLabel("Username").fill(apiUsername);
  await page.getByLabel("Password").fill(apiPassword);
  await page.getByRole("button", { name: "Sign in" }).click();

  await expect(page).toHaveURL(/\/overview$/);
  await expectPageHeading(page, "Overview Dashboard");
  await expect(page.getByTestId("aegiscore-logo")).toHaveCount(2);
  await expect(page.getByTestId("aegiscore-logo").first()).toBeVisible();
  await expect(page.getByTestId("aegiscore-logo").nth(1)).toBeVisible();
});

test("login route shows clear error on invalid credentials", async ({ page }) => {
  await clearStoredSession(page);
  await page.goto("/login");

  await page.getByLabel("Username").fill("admin");
  await page.getByLabel("Password").fill("incorrect-password");
  await page.getByRole("button", { name: "Sign in" }).click();

  await expect(page).toHaveURL(/\/login$/);
  await expect(
    page.getByText("Invalid username or password")
  ).toBeVisible();
});

test("invalid stored session is redirected back to login", async ({ page }) => {
  await page.addInitScript(() => {
    window.localStorage.setItem("aegiscore.access_token", "expired-or-invalid-token");
  });
  await page.goto("/overview");
  await expect(page).toHaveURL(/\/login$/);
  await expectPageHeading(page, "Sign in to AegisCore");
});

test("overview, alerts, and incidents support route-level investigation workflows", async ({
  page,
  request
}) => {
  await attachAuthenticatedSession(page, request);
  await page.goto("/overview");

  await expectPageHeading(page, "Overview Dashboard");
  await expect(page.getByRole("button", { name: "Refresh overview" })).toBeVisible();

  await page
    .locator('nav[aria-label="Primary"]')
    .getByRole("button")
    .filter({ hasText: "Alerts" })
    .click();
  await expect(page).toHaveURL(/\/alerts$/);
  await expectPageHeading(page, "Alerts");
  await page
    .getByLabel("Filter alerts by detection type")
    .selectOption("brute_force");
  await expect(
    page.getByLabel("Filter alerts by detection type")
  ).toHaveValue("brute_force");
  await expect(page.getByText("Alert triage filters")).toBeVisible();

  await page
    .locator('nav[aria-label="Primary"]')
    .getByRole("button")
    .filter({ hasText: "Incidents" })
    .click();
  await expect(page).toHaveURL(/\/incidents$/);
  await expectPageHeading(page, "Incidents Queue");
  await page
    .getByLabel("Filter incidents by detection type")
    .selectOption("brute_force");
  await expect(
    page.getByLabel("Filter incidents by detection type")
  ).toHaveValue("brute_force");
  await expect(page.getByText("Incident queue filters")).toBeVisible();
});

test("assets, responses, rules, and reports render live backend-backed operational data", async ({
  page,
  request
}) => {
  await attachAuthenticatedSession(page, request);
  await page.goto("/assets");

  await expectPageHeading(page, "Assets / Endpoints");

  await page
    .locator('nav[aria-label="Primary"]')
    .getByRole("button")
    .filter({ hasText: "Responses" })
    .click();
  await expect(page).toHaveURL(/\/responses$/);
  await expectPageHeading(page, "Response History");
  await expect(
    page
      .getByRole("table", { name: "Response history table" })
      .or(page.getByText("No response executions match the current filters"))
      .first()
  ).toBeVisible();

  await page
    .locator('nav[aria-label="Primary"]')
    .getByRole("button")
    .filter({ hasText: "Rules" })
    .click();
  await expect(page).toHaveURL(/\/rules$/);
  await expectPageHeading(page, "Rules / Policies");
  await expect(
    page.getByRole("table", { name: "Automated response policies table" })
  ).toBeVisible();
  await expect(page.getByText("real backend policies")).toBeVisible();

  await page
    .locator('nav[aria-label="Primary"]')
    .getByRole("button")
    .filter({ hasText: "Reports" })
    .click();
  await expect(page).toHaveURL(/\/reports$/);
  await expectPageHeading(page, "Reports");
  await expect(page.getByText("Operational data exports")).toBeVisible();

  const downloadPromise = page.waitForEvent("download");
  await page.getByRole("button", { name: "Export alerts" }).click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toContain("aegiscore-alerts-export");
});
