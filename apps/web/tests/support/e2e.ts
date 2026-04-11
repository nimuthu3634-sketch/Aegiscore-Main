import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import type { APIRequestContext, Page } from "@playwright/test";
import { expect } from "@playwright/test";

const accessTokenStorageKey = "aegiscore.access_token";
const sessionRoleStorageKey = "aegiscore.session_role";
const apiUsername = process.env.PLAYWRIGHT_API_USERNAME ?? "admin";
const apiPassword = process.env.PLAYWRIGHT_API_PASSWORD ?? "AegisCore123!";
const analystUsername = process.env.PLAYWRIGHT_ANALYST_USERNAME ?? "analyst";
const analystPassword = process.env.PLAYWRIGHT_ANALYST_PASSWORD ?? "AegisCore123!";
const fixturesDir = path.resolve(
  process.cwd(),
  "../api/tests/fixtures/ingestion"
);

export type ScenarioKey =
  | "brute_force"
  | "port_scan"
  | "file_integrity_violation"
  | "unauthorized_user_creation";

type ScenarioDefinition = {
  key: ScenarioKey;
  fixtureFile: string;
  source: "wazuh" | "suricata";
  detectionType: string;
  expectedSourceLabel: string;
  expectedResponseText: string;
  expectedEvidenceText: string;
};

type LoginApiResponse = {
  access_token: string;
};

type IngestionApiResponse = {
  alert: {
    id: string;
    detection_type: string;
  };
  linked_incident?: {
    id: string;
  } | null;
};

export type SeededScenario = {
  alertId: string;
  incidentId: string | null;
  detectionType: string;
  source: "wazuh" | "suricata";
  expectedSourceLabel: string;
  expectedResponseText: string;
  expectedEvidenceText: string;
};

const scenarioDefinitions: ScenarioDefinition[] = [
  {
    key: "brute_force",
    fixtureFile: "wazuh_brute_force.json",
    source: "wazuh",
    detectionType: "brute_force",
    expectedSourceLabel: "Wazuh",
    expectedResponseText: "block ip",
    expectedEvidenceText: "203.0.113.88"
  },
  {
    key: "port_scan",
    fixtureFile: "suricata_port_scan.json",
    source: "suricata",
    detectionType: "port_scan",
    expectedSourceLabel: "Suricata",
    expectedResponseText: "notify admin",
    expectedEvidenceText: "3389"
  },
  {
    key: "file_integrity_violation",
    fixtureFile: "wazuh_file_integrity_violation.json",
    source: "wazuh",
    detectionType: "file_integrity_violation",
    expectedSourceLabel: "Wazuh",
    expectedResponseText: "manual review",
    expectedEvidenceText: "D:\\Operations\\Policies\\access-control.xlsx"
  },
  {
    key: "unauthorized_user_creation",
    fixtureFile: "wazuh_unauthorized_user_creation.json",
    source: "wazuh",
    detectionType: "unauthorized_user_creation",
    expectedSourceLabel: "Wazuh",
    expectedResponseText: "notify admin",
    expectedEvidenceText: "unknown-admin"
  }
];

function withUniqueExternalId(
  payload: Record<string, unknown>,
  source: "wazuh" | "suricata",
  suffix: string
) {
  const cloned = structuredClone(payload);

  if (source === "wazuh") {
    if (typeof cloned.id === "string") {
      cloned.id = `${cloned.id}-${suffix}`;
    }

    const data = cloned.data;
    if (
      data &&
      typeof data === "object" &&
      !Array.isArray(data) &&
      typeof data.event_id === "string"
    ) {
      data.event_id = `${data.event_id}-${suffix}`;
    }
  }

  if (source === "suricata" && typeof cloned.flow_id === "string") {
    cloned.flow_id = `${cloned.flow_id}-${suffix}`;
  }

  return cloned;
}

function loadFixturePayload(
  fixtureFile: string,
  source: "wazuh" | "suricata"
) {
  const payload = JSON.parse(
    fs.readFileSync(path.join(fixturesDir, fixtureFile), "utf-8")
  ) as Record<string, unknown>;

  return withUniqueExternalId(payload, source, crypto.randomUUID().slice(0, 8));
}

export async function loginByApi(request: APIRequestContext) {
  return loginByApiWithCredentials(request, apiUsername, apiPassword);
}

export async function loginByApiWithCredentials(
  request: APIRequestContext,
  username: string,
  password: string
) {
  const response = await request.post("/api/auth/login", {
    data: {
      username,
      password
    }
  });

  expect(response.ok()).toBeTruthy();
  const payload = (await response.json()) as LoginApiResponse;
  return payload.access_token;
}

export async function attachAuthenticatedSession(
  page: Page,
  request: APIRequestContext,
  credentials: { username: string; password: string } = {
    username: apiUsername,
    password: apiPassword
  }
) {
  const token = await loginByApiWithCredentials(
    request,
    credentials.username,
    credentials.password
  );
  const roleName =
    credentials.username.toLowerCase() === analystUsername.toLowerCase()
      ? "analyst"
      : "admin";
  await page.addInitScript(
    ([storageKey, roleKey, accessToken, sessionRole]) => {
      window.localStorage.setItem(storageKey, accessToken);
      window.localStorage.setItem(roleKey, sessionRole);
    },
    [accessTokenStorageKey, sessionRoleStorageKey, token, roleName]
  );
  return token;
}

export async function clearStoredSession(page: Page) {
  await page.addInitScript(([storageKey, roleKey]) => {
    window.localStorage.removeItem(storageKey);
    window.localStorage.removeItem(roleKey);
  }, [accessTokenStorageKey, sessionRoleStorageKey]);
}

export async function seedThreatScenarios(
  request: APIRequestContext
): Promise<Record<ScenarioKey, SeededScenario>> {
  const token = await loginByApi(request);
  const seeded = {} as Record<ScenarioKey, SeededScenario>;

  for (const scenario of scenarioDefinitions) {
    const response = await request.post(
      `/api/integrations/${scenario.source}/events`,
      {
        data: loadFixturePayload(scenario.fixtureFile, scenario.source),
        headers: {
          Authorization: `Bearer ${token}`
        }
      }
    );

    expect(response.ok()).toBeTruthy();
    const payload = (await response.json()) as IngestionApiResponse;

    seeded[scenario.key] = {
      alertId: payload.alert.id,
      incidentId: payload.linked_incident?.id ?? null,
      detectionType: payload.alert.detection_type,
      source: scenario.source,
      expectedSourceLabel: scenario.expectedSourceLabel,
      expectedResponseText: scenario.expectedResponseText,
      expectedEvidenceText: scenario.expectedEvidenceText
    };
  }

  return seeded;
}

export async function expectPageHeading(page: Page, title: string) {
  await expect(page.getByRole("heading", { name: title })).toBeVisible();
}

export { apiPassword, apiUsername };
export { analystPassword, analystUsername };
