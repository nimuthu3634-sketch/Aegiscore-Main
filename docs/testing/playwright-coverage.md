# Playwright Coverage

Browser tests support the **MVP** product posture (**single-tenant**, **SME/lab**): they validate the real console against the four supported detections and **operator write paths**—not unlimited enterprise SOC breadth.

## Operator workflow proof (checklist)

These are the **intentionally covered** operator-relevant flows and where they are asserted. All require a **running API** (see Runbook).

| # | Flow | Proof | Test file (test name) |
|---|------|--------|-------------------------|
| 1 | Login success | UI navigates to `/overview` after valid credentials | `core-workflows.spec.ts` — *login route authenticates and opens the overview dashboard* |
| 2 | Login failure | Stays on `/login`, shows invalid-credentials copy | `core-workflows.spec.ts` — *login route shows clear error on invalid credentials* |
| 3 | Alert acknowledge | Success message in `alert-workflow-feedback` | `write-workflows.spec.ts` — *alerts support acknowledge, close, note, and link-to-incident write flows* |
| 4 | Alert close | Success message in `alert-workflow-feedback` | same |
| 5 | Link alert → existing incident | Modal: search by incident id, select candidate, enabled confirm, success toast | same (skipped when no unlinked alert or no incident id) |
| 6 | Create new incident from alert | New-incident mode + confirm | same |
| 7 | Add analyst note | Note text visible after save | same |
| 8 | Incident transition | Success copy in `incident-transition-feedback` | `write-workflows.spec.ts` — *incident transitions, policy toggles, and reports export trigger stay operational* |
| 9 | Policy enable / disable | Toggle twice; success toast copy each time | same |
| 10 | Report export trigger | Incidents export (JSON) download or inline export message | same; **alerts** CSV export in `core-workflows.spec.ts` — *assets, responses, rules, and reports…* |
| 11 | Notification visibility | Incident panel + linked-alert panel; responses table or empty | `notification-and-negative-paths.spec.ts` — *notification panels render…* |
| 12 | Not-found detail routes | `detail-record-not-found` on unknown alert/incident UUID | `notification-and-negative-paths.spec.ts` — *detail routes show not-found…* |
| 13 | Forbidden / role-restricted | Analyst: disabled policy toggles + `policy-admin-only-hint`; API `PATCH` returns 403 | `write-workflows.spec.ts` — *analyst role cannot mutate policy enabled state* |
| 14 | Failed mutation (client) | Empty note → `analyst-notes-feedback` validation | `notification-and-negative-paths.spec.ts` — *analyst note save rejects empty draft…* |
| 15 | Failed mutation (simulated API) | Route stub `503` on acknowledge → `alert-workflow-feedback` shows `detail` | `operator-workflows.spec.ts` — *alert acknowledge surfaces server error in workflow feedback* |

Additional **negative / API** coverage (not only UI): invalid incident transition returns `400/409` with *cannot transition* in body — `write-workflows.spec.ts` — *incident transition invalid action is rejected…*

Per-detection **read + evidence** paths: `scenario-coverage.spec.ts` (four scenarios).

## Root cause (historical)

The earlier Playwright gap was not a missing test directory. The real root causes were:

- the old smoke test had drifted away from the current routed application
- Playwright was running against `vite preview`, which did not mirror the intended local `/api` development proxy path
- the frontend did not yet expose a real `/login` route for browser-authenticated workflow coverage
- scenario seeding could collide with duplicate-ingestion protection and accidentally validate stale alerts instead of the fresh end-to-end path

## Fixes applied (stack)

- `apps/web/playwright.config.ts`
  - switched Playwright to the Vite dev server
  - pinned the test server to `127.0.0.1:4173`
  - set `workers: 1` for stable backend-mutating coverage
  - used `/login` as the server readiness URL
- `apps/web/vite.config.ts`
  - added a real `/api` proxy to the backend
  - enabled `strictPort` for predictable Playwright startup
- `apps/web/src/App.tsx`
  - added the real `/login` route
  - skipped dashboard health-shell behavior on the standalone login route
- `apps/web/src/pages/LoginPage.tsx`
  - added browser-testable login UX
- `apps/web/tests/support/e2e.ts`
  - added authenticated-session helpers
  - added live scenario seeding with unique external identifiers per run

## Stable `data-testid` hooks (browser tests)

| Hook | Purpose |
|------|---------|
| `detail-record-not-found` | Alert/incident detail routes when the record is missing |
| `incident-notifications-panel` / `alert-notifications-panel` | Administrator notification sections on detail pages |
| `alert-notification-link-required` | Alert not linked to an incident (notifications scoped to incidents) |
| `notification-event-row` / `notification-empty-state` | Notification history rows or empty copy inside those panels |
| `alert-workflow-feedback` | Acknowledge/close/link workflow success or error message on alert detail |
| `incident-transition-feedback` | Incident state transition success or error message |
| `analyst-notes-feedback` | Analyst note save validation or success copy |
| `response-linked-notification-deliveries` / `response-notification-delivery-item` | Nested delivery list on related response cards |
| `response-row-notification-summary` | Optional delivery summary line in the responses list table |
| `policy-admin-only-hint` | Analyst read-only explanation on Rules / Policies |
| `alert-acknowledge-btn` / `alert-close-btn` / `alert-link-incident-btn` | Alert lifecycle actions |
| `link-incident-*` | Link modal mode, search, candidates, confirm |
| `policy-toggle-*` | Per-row policy enable/disable control |
| `incident-transition-*-btn` | Incident workflow buttons |

## Test files

- `apps/web/tests/core-workflows.spec.ts` — login, session redirect, navigation, alerts/incidents filters, assets/responses/rules/reports, **alerts export**
- `apps/web/tests/scenario-coverage.spec.ts` — four detection scenarios end-to-end
- `apps/web/tests/write-workflows.spec.ts` — **serial** alert/incident/policy/report **mutations** + analyst forbidden path + invalid transition API check
- `apps/web/tests/notification-and-negative-paths.spec.ts` — not-found, empty-note validation, notification panels + responses list
- `apps/web/tests/operator-workflows.spec.ts` — **deterministic** simulated API failure on acknowledge (Playwright `route`)
- `apps/web/tests/support/e2e.ts`

## Runbook

Playwright starts the Vite dev server and proxies `/api` to **`http://127.0.0.1:8000`**. **Without the API, tests fail immediately** (login/seed cannot run). Start the API (for example `docker compose up -d api`), apply migrations if needed, and seed users so login succeeds:

```powershell
docker compose exec api python -m app.db.seed
npm run test:web:e2e
```

### Latest recorded run

Update this line when you record a full green run in CI or locally:

- *(local):* run `npm run test:web:e2e` with API up; expect **17** tests (or fewer if conditional skips apply—see below).

### Conditional skips (honest branch coverage)

In **other** environments (empty DB, missing incidents, or no alerts linked to incidents), the following may skip or narrow assertions:

- `notification-and-negative-paths.spec.ts` — combined notification/responses test skips when no incident exists or no alert has an incident link.
- `write-workflows.spec.ts` — incident transition, policy toggle, export, and invalid-transition tests skip when no non-terminal incident candidate exists after seeding.
- Link-to-existing requires a visible non-terminal incident row after search; if the list omits the target id, the step fails fast (no silent cancel).

These branches are **data-dependent**, not flaky styling tests; a healthy seeded lab run should execute them.

## Intentionally not covered (exclusions)

- **No** dedicated response **detail** route in the UI; list-row notification summaries are optional when the API omits `notificationSummary`.
- **Related responses** nested `related_notifications` blocks are not separately asserted unless the fixture set returns them.
- **Export file content** is not parsed in the browser (only download filename or UI export message).
- **Role matrix**: only one forbidden path is proven in browser + API (`PATCH /policies/{id}` as analyst); other admin-only endpoints are not exhaustively negative-tested in Playwright.
- **Invalid transition matrix**: one invalid action + API assertion; not every state/action permutation.
- **Cosmetic / pixel** assertions are avoided; copy may evolve if product strings change—prefer `data-testid` and stable API messages where listed above.
- **Simulated acknowledge failure** (`operator-workflows.spec.ts`) proves the **error surface**, not production outage behavior.

## Future coverage work

- Additional admin-only surfaces if new UI mutations ship.
- Export payload validation in **API** tests rather than Playwright.
