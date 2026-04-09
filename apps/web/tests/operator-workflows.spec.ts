import { expect, test } from "@playwright/test";
import {
  attachAuthenticatedSession,
  loginByApi,
  seedThreatScenarios
} from "./support/e2e";

/**
 * Deterministic browser proof for operator-visible API failures (not only happy paths).
 * Complements integration-style tests in write-workflows.spec.ts.
 */
test.describe.configure({ mode: "serial", timeout: 120000 });

test.beforeAll(async ({ request }) => {
  await seedThreatScenarios(request);
});

type AlertsListItem = {
  id: string;
  status_label: string;
};

type AlertsListApiResponse = {
  items: AlertsListItem[];
};

test("alert acknowledge surfaces server error in workflow feedback", async ({
  page,
  request
}) => {
  const token = await loginByApi(request);
  const alertsResponse = await request.get(
    "/api/alerts?page=1&page_size=50&date_range=all",
    { headers: { Authorization: `Bearer ${token}` } }
  );
  expect(alertsResponse.ok()).toBeTruthy();
  const body = (await alertsResponse.json()) as AlertsListApiResponse;
  const ackable = body.items.find(
    (item) =>
      !["investigating", "resolved"].includes(item.status_label.toLowerCase())
  );
  expect(ackable).toBeTruthy();

  await attachAuthenticatedSession(page, request);

  let intercepted = 0;
  await page.route("**/api/alerts/*/acknowledge", async (route) => {
    intercepted += 1;
    await route.fulfill({
      status: 503,
      contentType: "application/json",
      body: JSON.stringify({
        detail: "Playwright simulated acknowledge failure"
      })
    });
  });

  await page.goto(`/alerts/${ackable!.id}`);
  await page.getByTestId("alert-acknowledge-btn").click();
  await expect(page.getByTestId("alert-workflow-feedback")).toContainText(
    "Playwright simulated acknowledge failure"
  );
  expect(intercepted).toBe(1);
});
