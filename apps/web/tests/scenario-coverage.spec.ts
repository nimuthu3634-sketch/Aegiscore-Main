import { expect, test } from "@playwright/test";
import { formatTokenLabel } from "../src/lib/formatters";
import {
  attachAuthenticatedSession,
  expectPageHeading,
  seedThreatScenarios,
  type ScenarioKey,
  type SeededScenario
} from "./support/e2e";

/** Policy action type labels as rendered on Response History (matches `formatTokenLabel` on API snake_case). */
const scenarioResponseActionLabel: Record<ScenarioKey, string> = {
  brute_force: formatTokenLabel("block_ip"),
  file_integrity_violation: formatTokenLabel("create_manual_review"),
  port_scan: formatTokenLabel("notify_admin"),
  unauthorized_user_creation: formatTokenLabel("notify_admin")
};

let seededScenarios: Record<ScenarioKey, SeededScenario>;

test.describe.configure({ mode: "serial", timeout: 120000 });

test.beforeAll(async ({ request }) => {
  seededScenarios = await seedThreatScenarios(request);
});

const scenarioKeys: ScenarioKey[] = [
  "brute_force",
  "file_integrity_violation",
  "port_scan",
  "unauthorized_user_creation"
];

for (const scenarioKey of scenarioKeys) {
  test(`supported threat scenario ${scenarioKey} is visible through live alert detail, incident detail, and reports`, async ({
    page,
    request
  }) => {
    const scenario = seededScenarios[scenarioKey];

    await attachAuthenticatedSession(page, request);

    await page.goto("/overview");
    await expectPageHeading(page, "Overview Dashboard");
    await expect(
      page.getByText(
        `${formatTokenLabel(scenario.detectionType)}: `,
        { exact: false }
      )
    ).toBeVisible();

    await page.goto("/alerts");
    await expectPageHeading(page, "Alerts");
    await page.getByLabel("Filter alerts by detection type").selectOption(scenario.detectionType);
    await expect(page.getByText(formatTokenLabel(scenario.detectionType)).first()).toBeVisible();

    await page.goto(`/alerts/${scenario.alertId}`);

    await expectPageHeading(page, formatTokenLabel(scenario.detectionType));
    await expect(page.getByText("Scoring method")).toBeVisible();
    await expect(page.getByText("Top drivers")).toBeVisible();
    await expect(
      page.getByText(scenario.expectedSourceLabel, { exact: true }).first()
    ).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "Related response actions" })
    ).toBeVisible();
    await expect(
      page.getByText(scenario.expectedEvidenceText, { exact: false }).first()
    ).toBeVisible();

    if (scenario.incidentId) {
      await page.goto("/incidents");
      await expectPageHeading(page, "Incidents Queue");
      await page
        .getByLabel("Filter incidents by detection type")
        .selectOption(scenario.detectionType);
      await expect(
        page.getByRole("table", { name: "Incidents queue table" })
      ).toBeVisible();
      await expect(page.getByText(formatTokenLabel(scenario.detectionType)).first()).toBeVisible();

      await page.goto(`/incidents/${scenario.incidentId}`);
      await expect(
        page.getByRole("heading", { name: "Linked alerts" })
      ).toBeVisible();
      await expect(
        page.getByRole("heading", { name: "Response action history" })
      ).toBeVisible();
      await expect(
        page.getByRole("table", { name: "Linked alerts table" })
      ).toBeVisible();
    }

    await page.goto("/responses");
    await expectPageHeading(page, "Response History");
    await expect(
      page.getByRole("table", { name: "Response history table" })
    ).toBeVisible();
    await expect(
      page.getByText(scenarioResponseActionLabel[scenarioKey]).first()
    ).toBeVisible();

    await page.goto("/reports");
    await page.getByLabel("Filter reports by detection type").selectOption(
      scenario.detectionType
    );
    await expect(
      page.getByText("Daily alerts", { exact: true }).first()
    ).toBeVisible();
    await expect(
      page.getByText("Operational data exports", { exact: false })
    ).toBeVisible();
  });
}
