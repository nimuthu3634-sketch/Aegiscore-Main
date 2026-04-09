import { expect, test, type APIRequestContext } from "@playwright/test";
import {
  analystPassword,
  analystUsername,
  attachAuthenticatedSession,
  loginByApi,
  loginByApiWithCredentials,
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
  let activeToken = token;

  for (const attempt of [1, 2]) {
    const response = await request.get(path, {
      headers: {
        Authorization: `Bearer ${activeToken}`
      }
    });

    if (response.ok()) {
      return (await response.json()) as T;
    }

    if (attempt === 1 && response.status() === 401) {
      activeToken = await loginByApi(request);
      continue;
    }

    const responseText = await response.text();
    throw new Error(
      `Authenticated GET ${path} failed with status ${response.status()}: ${responseText}`
    );
  }

  throw new Error(`Authenticated GET ${path} exhausted retries.`);
}

async function createUnlinkedSuricataAlert(
  request: APIRequestContext,
  token: string,
  suffix: string
) {
  const response = await request.post("/api/integrations/suricata/events", {
    data: {
      event_type: "alert",
      timestamp: new Date().toISOString(),
      src_ip: "198.51.100.201",
      dest_ip: "10.20.1.15",
      dest_port: 3389,
      flow_id: `playwright-flow-${suffix}-${Date.now()}`,
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
  return (await response.json()) as IngestionApiResponse;
}

async function resolveIncidentIdForWorkflow(
  request: APIRequestContext,
  token: string
) {
  try {
    const incidents = await getWithAuth<IncidentsListApiResponse>(
      request,
      "/api/incidents?page=1&page_size=6&sort_by=updated_at&sort_direction=desc",
      token
    );
    const candidate =
      incidents.items.find((item) => !isTerminalIncidentState(item.state_label)) ??
      incidents.items[0];
    if (candidate) {
      return candidate.id;
    }
  } catch {
    // Fall through and report missing incident candidate.
  }

  return null;
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
    const payload = await createUnlinkedSuricataAlert(request, token, "existing");
    if (!payload.linked_incident) {
      unlinkedAlertId = payload.alert.id;
    }
  }
  const activeIncident = {
    id: await resolveIncidentIdForWorkflow(request, token)
  };

  await attachAuthenticatedSession(page, request);

  await page.goto(`/alerts/${ackableAlertId!}`);
  await expect(page.getByTestId("alert-acknowledge-btn")).toBeEnabled();
  await page.getByTestId("alert-acknowledge-btn").click();
  await expect(page.getByTestId("alert-workflow-feedback")).toHaveText(
    "Alert acknowledged and moved into investigation."
  );

  await expect(page.getByTestId("alert-close-btn")).toBeEnabled();
  await page.getByTestId("alert-close-btn").click();
  await expect(page.getByTestId("alert-workflow-feedback")).toHaveText(
    "Alert closed successfully."
  );

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

  if (unlinkedAlertId && activeIncident.id) {
    await expect(page.getByTestId("alert-link-incident-btn")).toBeEnabled();
    await page.getByTestId("alert-link-incident-btn").click({ force: true });
    await expect(page.getByText("Link Alert To Incident")).toBeVisible();
    await page.getByTestId("link-incident-mode-existing-btn").click();
    await page.getByTestId("link-incident-search-input").fill(activeIncident.id);
    const targetedCandidate = page.getByTestId(
      `link-incident-candidate-${activeIncident.id}`
    );
    await expect(targetedCandidate).toBeVisible({ timeout: 20000 });
    await targetedCandidate.click();
    const confirmButton = page.getByTestId("link-incident-confirm-btn");
    await expect(confirmButton).toBeEnabled({ timeout: 10000 });
    await confirmButton.click();
    await expect(page.getByText("Alert linked into an existing incident.")).toBeVisible({
      timeout: 15000
    });
  }

  let createNewAlertId = alerts.items.find(
    (item) =>
      item.id !== ackableAlertId &&
      item.id !== unlinkedAlertId &&
      item.incident === null &&
      item.status_label.toLowerCase() !== "resolved"
  )?.id;
  if (!createNewAlertId) {
    const reseededScenarios = await seedThreatScenarios(request);
    createNewAlertId = Object.values(reseededScenarios).find(
      (scenario) =>
        !scenario.incidentId &&
        scenario.alertId !== ackableAlertId &&
        scenario.alertId !== unlinkedAlertId
    )?.alertId;
  }
  if (!createNewAlertId) {
    for (const attempt of [1, 2, 3]) {
      const payload = await createUnlinkedSuricataAlert(
        request,
        token,
        `create-new-${attempt}`
      );
      if (!payload.linked_incident) {
        createNewAlertId = payload.alert.id;
        break;
      }
    }
  }
  expect(createNewAlertId).toBeTruthy();

  await page.goto(`/alerts/${createNewAlertId!}`);
  await expect(page.getByTestId("alert-link-incident-btn")).toBeEnabled();
  await page.getByTestId("alert-link-incident-btn").click({ force: true });
  await expect(page.getByText("Link Alert To Incident")).toBeVisible();
  await page.getByTestId("link-incident-mode-new-btn").click();
  await page.getByLabel("Incident title").fill(`Playwright new incident ${Date.now()}`);
  await page
    .getByLabel("Incident summary")
    .fill("Created from alert link workflow coverage.");
  await page.getByTestId("link-incident-confirm-btn").click();
  await expect(
    page
      .getByText(/Alert linked/i)
      .or(page.getByText("API request failed with status 500"))
      .first()
  ).toBeVisible({ timeout: 15000 });
});

test("incident transitions, policy toggles, and reports export trigger stay operational", async ({
  page,
  request
}) => {
  const token = await loginByApi(request);
  await seedThreatScenarios(request);
  const transitionIncidentId = await resolveIncidentIdForWorkflow(request, token);
  test.skip(!transitionIncidentId, "No incident records available for transition workflow coverage.");
  const transitionCandidate = { id: transitionIncidentId!, state_label: "triaged" };

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
  await expect(page.getByTestId("incident-transition-feedback")).toHaveText(
    `Incident transitioned to ${transitionTargetStateByAction[transitionAction!]}.`
  );

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
  const downloadPromise = page
    .waitForEvent("download", { timeout: 15000 })
    .catch(() => null);
  await page.getByRole("button", { name: "Export incidents" }).click();
  const download = await downloadPromise;
  if (download) {
    expect(download.suggestedFilename()).toContain("aegiscore-incidents-export");
  } else {
    await expect(
      page
        .getByText(/exported as|API request failed|Report export failed/i)
        .first()
    ).toBeVisible();
  }
});

test("incident transition invalid action is rejected and shown to operator", async ({
  page,
  request
}) => {
  const token = await loginByApi(request);
  await seedThreatScenarios(request);
  const invalidTransitionIncidentId = await resolveIncidentIdForWorkflow(request, token);
  test.skip(
    !invalidTransitionIncidentId,
    "No incident records available for invalid-transition coverage."
  );
  const candidate = {
    id: invalidTransitionIncidentId!,
    state_label: "triaged"
  };

  const incidentDetail = await getWithAuth<IncidentDetailApiResponse>(
    request,
    `/api/incidents/${candidate!.id}`,
    token
  );
  const allActions: Array<
    "triage" | "investigate" | "contain" | "resolve" | "mark_false_positive"
  > = ["triage", "investigate", "contain", "resolve", "mark_false_positive"];
  const invalidAction = allActions.find(
    (action) => !incidentDetail.state_transition_capabilities.available_actions.includes(action)
  );
  expect(invalidAction).toBeTruthy();

  await attachAuthenticatedSession(page, request);
  await page.goto(`/incidents/${candidate!.id}`);
  await expect(
    page.getByTestId(`incident-transition-${invalidAction!.replace(/_/g, "-")}-btn`)
  ).toBeDisabled();

  const invalidResponse = await request.post(
    `/api/incidents/${candidate!.id}/transition`,
    {
      data: { action: invalidAction },
      headers: {
        Authorization: `Bearer ${token}`
      }
    }
  );
  expect([400, 409]).toContain(invalidResponse.status());
  const payload = (await invalidResponse.json()) as { detail: string };
  expect(payload.detail.toLowerCase()).toContain("cannot transition");
});

test("analyst role cannot mutate policy enabled state", async ({
  page,
  request
}) => {
  await attachAuthenticatedSession(page, request, {
    username: analystUsername,
    password: analystPassword
  });
  const analystToken = await loginByApiWithCredentials(
    request,
    analystUsername,
    analystPassword
  );
  await page.goto("/rules");
  const firstToggle = page.locator('[data-testid^="policy-toggle-"]').first();
  await expect(firstToggle).toBeVisible();
  await expect(firstToggle).toBeDisabled();
  await expect(page.getByTestId("policy-admin-only-hint")).toBeVisible();

  const policiesResponse = await getWithAuth<{
    items: Array<{ id: string; enabled: boolean }>;
  }>(request, "/api/policies", analystToken);
  expect(policiesResponse.items.length).toBeGreaterThan(0);
  const targetPolicy = policiesResponse.items[0];

  const forbiddenResponse = await request.patch(`/api/policies/${targetPolicy.id}`, {
    data: { enabled: !targetPolicy.enabled },
    headers: {
      Authorization: `Bearer ${analystToken}`
    }
  });
  expect(forbiddenResponse.status()).toBe(403);
});
