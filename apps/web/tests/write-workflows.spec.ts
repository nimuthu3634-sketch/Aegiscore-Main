import { expect, test, type APIRequestContext } from "@playwright/test";
import {
  attachAuthenticatedSession,
  loginByApi,
  seedThreatScenarios
} from "./support/e2e";

type AlertListItem = {
  id: string;
  detection_type: string;
  status_label: string;
  incident: { id: string } | null;
};

type AlertsListApiResponse = {
  items: AlertListItem[];
};

type IncidentListItem = {
  id: string;
  state_label: string;
};

type IncidentsListApiResponse = {
  items: IncidentListItem[];
};

type IncidentDetailApiResponse = {
  state_transition_capabilities: {
    available_actions: Array<
      "triage" | "investigate" | "contain" | "resolve" | "mark_false_positive"
    >;
  };
};

type AlertDetailApiResponse = {
  id: string;
  status_label: string;
};

type IngestionApiResponse = {
  alert: { id: string };
  linked_incident?: { id: string } | null;
};

const transitionTargetStateByAction = {
  triage: "triaged",
  investigate: "investigating",
  contain: "contained",
  resolve: "resolved",
  mark_false_positive: "false_positive"
} as const;

function isTerminalIncidentState(stateLabel: string) {
  const normalized = stateLabel.toLowerCase();
  return normalized === "resolved" || normalized === "false positive" || normalized === "false_positive";
}

test.describe.configure({ mode: "serial", timeout: 120000 });

test.beforeAll(async ({ request }) => {
  await seedThreatScenarios(request);
});

async function getWithAuth<T>(
  request: APIRequestContext,
  path: string,
  token: string
) {
  const response = await request.get(path, {
    headers: {
      Authorization: `Bearer ${token}`
    }
  });
  expect(response.ok()).toBeTruthy();
  return (await response.json()) as T;
}

test("alerts support acknowledge, close, note, and link-to-incident write flows", async ({
  page,
  request
}) => {
  const token = await loginByApi(request);
  const seededScenarios = await seedThreatScenarios(request);
  const alerts = await getWithAuth<AlertsListApiResponse>(
    request,
    "/api/alerts?page=1&page_size=100&date_range=all",
    token
  );
  const incidents = await getWithAuth<IncidentsListApiResponse>(
    request,
    "/api/incidents?page=1&page_size=100",
    token
  );

  const ackableAlert = alerts.items.find((item) =>
    !["investigating", "resolved"].includes(item.status_label.toLowerCase())
  );
  let ackableAlertId = ackableAlert?.id;
  if (!ackableAlertId) {
    for (const seededScenario of Object.values(seededScenarios)) {
      const seededAlert = await getWithAuth<AlertDetailApiResponse>(
        request,
        `/api/alerts/${seededScenario.alertId}`,
        token
      );
      if (!["investigating", "resolved"].includes(seededAlert.status_label.toLowerCase())) {
        ackableAlertId = seededScenario.alertId;
        break;
      }
    }
  }
  expect(ackableAlertId).toBeTruthy();

  const unlinkedAlert = alerts.items.find(
    (item) =>
      item.id !== ackableAlertId &&
      item.incident === null &&
      item.status_label.toLowerCase() !== "resolved"
  );
  const seededUnlinkedAlert = Object.values(seededScenarios).find(
    (scenario) => !scenario.incidentId && scenario.alertId !== ackableAlertId
  );
  let unlinkedAlertId = unlinkedAlert?.id ?? seededUnlinkedAlert?.alertId;
  if (!unlinkedAlertId) {
    const response = await request.post("/api/integrations/suricata/events", {
      data: {
        event_type: "alert",
        timestamp: new Date().toISOString(),
        src_ip: "198.51.100.201",
        dest_ip: "10.20.1.15",
        dest_port: 3389,
        flow_id: `playwright-flow-${Date.now()}`,
        alert: {
          signature_id: 2100498,
          signature: "ET SCAN Potential RDP Scan",
          category: "Attempted Information Leak",
          severity: 1
        }
      },
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    expect(response.ok()).toBeTruthy();
    const payload = (await response.json()) as IngestionApiResponse;
    if (!payload.linked_incident) {
      unlinkedAlertId = payload.alert.id;
    }
  }
  const activeIncident = incidents.items.find(
    (item) => !isTerminalIncidentState(item.state_label)
  );
  expect(activeIncident).toBeTruthy();

  await attachAuthenticatedSession(page, request);

  await page.goto(`/alerts/${ackableAlertId!}`);
  await expect(page.getByTestId("alert-acknowledge-btn")).toBeEnabled();
  await page.getByTestId("alert-acknowledge-btn").click();
  await expect(
    page.getByText("Alert acknowledged and moved into investigation.")
  ).toBeVisible();

  await expect(page.getByTestId("alert-close-btn")).toBeEnabled();
  await page.getByTestId("alert-close-btn").click();
  await expect(page.getByText("Alert closed successfully.")).toBeVisible();

  const noteTargetAlertId = unlinkedAlertId ?? ackableAlertId!;
  await page.goto(`/alerts/${noteTargetAlertId}`);
  const noteText = `Playwright alert note ${Date.now()}`;
  await page.getByTestId("analyst-notes-input").fill(noteText);
  const saveNoteButton = page.getByTestId("analyst-notes-save-btn");
  await saveNoteButton.scrollIntoViewIfNeeded();
  await saveNoteButton.click({ force: true });
  await expect(
    page
      .getByText("Alert note saved successfully.")
      .or(page.getByText(noteText))
      .first()
  ).toBeVisible({ timeout: 15000 });
  await expect(page.getByText(noteText)).toBeVisible();

  if (unlinkedAlertId) {
    await expect(page.getByTestId("alert-link-incident-btn")).toBeEnabled();
    await page.getByTestId("alert-link-incident-btn").click({ force: true });
    await expect(page.getByText("Link Alert To Incident")).toBeVisible();
    await page.getByTestId("link-incident-mode-existing-btn").click();
    await page
      .getByTestId("link-incident-search-input")
      .fill(activeIncident!.id);
    await page
      .getByTestId(`link-incident-candidate-${activeIncident!.id}`)
      .click();
    await page.getByTestId("link-incident-confirm-btn").click();
    await expect(page.getByText("Alert linked into an existing incident.")).toBeVisible();
  }
});

test("incident transitions, policy toggles, and reports export trigger stay operational", async ({
  page,
  request
}) => {
  const token = await loginByApi(request);
  const incidents = await getWithAuth<IncidentsListApiResponse>(
    request,
    "/api/incidents?page=1&page_size=100",
    token
  );

  const transitionCandidate = incidents.items.find(
    (item) => !isTerminalIncidentState(item.state_label)
  );
  expect(transitionCandidate).toBeTruthy();

  const incidentDetail = await getWithAuth<IncidentDetailApiResponse>(
    request,
    `/api/incidents/${transitionCandidate!.id}`,
    token
  );
  const transitionAction =
    incidentDetail.state_transition_capabilities.available_actions.find((action) =>
      ["investigate", "contain", "resolve", "triage", "mark_false_positive"].includes(action)
    );
  expect(transitionAction).toBeTruthy();

  await attachAuthenticatedSession(page, request);

  await page.goto(`/incidents/${transitionCandidate!.id}`);
  await page
    .getByTestId(`incident-transition-${transitionAction!.replace(/_/g, "-")}-btn`)
    .click();
  await expect(
    page.getByText(
      `Incident transitioned to ${transitionTargetStateByAction[transitionAction!]}.`
    )
  ).toBeVisible();

  await page.goto("/rules");
  const policyToggle = page.locator('[data-testid^="policy-toggle-"]').first();
  await expect(policyToggle).toBeVisible();
  await policyToggle.click();
  await expect(
    page.getByText(/Policy (enabled|disabled) successfully\./)
  ).toBeVisible();

  await policyToggle.click();
  await expect(
    page.getByText(/Policy (enabled|disabled) successfully\./)
  ).toBeVisible();

  await page.goto("/reports");
  await page.getByLabel("Select export format").selectOption("json");
  const downloadPromise = page.waitForEvent("download");
  await page.getByRole("button", { name: "Export incidents" }).click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toContain("aegiscore-incidents-export");
});
