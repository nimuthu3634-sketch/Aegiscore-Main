import { expect, test } from "@playwright/test";
import {
  attachAuthenticatedSession,
  loginByApi,
  seedThreatScenarios
} from "./support/e2e";

const UNKNOWN_RECORD_UUID = "00000000-0000-0000-0000-000000000001";

type AlertsListResponse = {
  items: Array<{ id: string; incident: { id: string } | null }>;
};

type IncidentsListResponse = {
  items: Array<{ id: string }>;
};

test.describe.configure({ mode: "serial", timeout: 120000 });

test.beforeAll(async ({ request }) => {
  await seedThreatScenarios(request);
});

test("detail routes show not-found empty state for unknown ids", async ({
  page,
  request
}) => {
  await attachAuthenticatedSession(page, request);

  await page.goto(`/alerts/${UNKNOWN_RECORD_UUID}`);
  await expect(page.getByTestId("detail-record-not-found")).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Alert record was not found" })
  ).toBeVisible();

  await page.goto(`/incidents/${UNKNOWN_RECORD_UUID}`);
  await expect(page.getByTestId("detail-record-not-found")).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Incident record was not found" })
  ).toBeVisible();
});

test("analyst note save rejects empty draft with visible validation feedback", async ({
  page,
  request
}) => {
  const token = await loginByApi(request);
  const alertsResponse = await request.get(
    "/api/alerts?page=1&page_size=5&date_range=all",
    {
      headers: { Authorization: `Bearer ${token}` }
    }
  );
  expect(alertsResponse.ok()).toBeTruthy();
  const alertsBody = (await alertsResponse.json()) as AlertsListResponse;
  expect(alertsBody.items.length).toBeGreaterThan(0);
  const alertId = alertsBody.items[0].id;

  await attachAuthenticatedSession(page, request);
  await page.goto(`/alerts/${alertId}`);
  await page.getByTestId("analyst-notes-input").fill("");
  await page.getByTestId("analyst-notes-save-btn").click();
  await expect(page.getByTestId("analyst-notes-feedback")).toHaveText(
    "Note content cannot be empty."
  );
});

test("notification panels render on incident and linked-alert detail; responses history is reachable", async ({
  page,
  request
}) => {
  const token = await loginByApi(request);

  const incidentsResponse = await request.get(
    "/api/incidents?page=1&page_size=10&sort_by=updated_at&sort_direction=desc",
    {
      headers: { Authorization: `Bearer ${token}` }
    }
  );
  expect(incidentsResponse.ok()).toBeTruthy();
  const incidentsBody = (await incidentsResponse.json()) as IncidentsListResponse;
  test.skip(
    incidentsBody.items.length === 0,
    "No incidents available for notification panel coverage."
  );
  const incidentId = incidentsBody.items[0].id;

  const alertsResponse = await request.get(
    "/api/alerts?page=1&page_size=100&date_range=all",
    {
      headers: { Authorization: `Bearer ${token}` }
    }
  );
  expect(alertsResponse.ok()).toBeTruthy();
  const alertsBody = (await alertsResponse.json()) as AlertsListResponse;
  const linkedAlert = alertsBody.items.find((item) => item.incident !== null);
  test.skip(
    !linkedAlert,
    "No alert linked to an incident for linked-alert notification coverage."
  );

  await attachAuthenticatedSession(page, request);

  await page.goto(`/incidents/${incidentId}`);
  await expect(page.getByTestId("incident-notifications-panel")).toBeVisible();
  await expect(
    page
      .getByTestId("notification-event-row")
      .or(page.getByTestId("notification-empty-state"))
      .first()
  ).toBeVisible();

  await page.goto(`/alerts/${linkedAlert!.id}`);
  await expect(page.getByTestId("alert-notifications-panel")).toBeVisible();
  await expect(page.getByTestId("alert-notification-link-required")).toHaveCount(0);
  await expect(
    page
      .getByTestId("notification-event-row")
      .or(page.getByTestId("notification-empty-state"))
      .first()
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Related response actions" })
  ).toBeVisible();

  await page.goto("/responses");
  const historyTable = page.getByRole("table", { name: "Response history table" });
  const responsesEmpty = page.getByRole("heading", {
    name: "No response executions match the current filters"
  });
  await expect(historyTable.or(responsesEmpty).first()).toBeVisible();
  if (
    (await historyTable.isVisible()) &&
    (await page.getByTestId("response-row-notification-summary").count()) > 0
  ) {
    await expect(
      page.getByTestId("response-row-notification-summary").first()
    ).toBeVisible();
  }
});
