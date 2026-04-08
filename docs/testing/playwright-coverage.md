# Playwright Coverage

Browser tests support the **final scoped v1** product (**single-tenant**, **SME/lab**): they validate the real console against the four supported detections and core workflows—not enterprise SOC breadth.

## Root Cause

The earlier Playwright gap was not a missing test directory. The real root causes were:

- the old smoke test had drifted away from the current routed application
- Playwright was running against `vite preview`, which did not mirror the intended local `/api` development proxy path
- the frontend did not yet expose a real `/login` route for browser-authenticated workflow coverage
- scenario seeding could collide with duplicate-ingestion protection and accidentally validate stale alerts instead of the fresh end-to-end path

## Fixes Applied

The coverage stack was corrected in these areas:

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

## Current Coverage

The Playwright suite now covers:

- login route
- login success
- login failure on invalid credentials
- invalid or expired session redirect to `/login`
- overview dashboard
- alerts list
- alert detail
- alert acknowledge
- alert close
- alert link to existing incident
- alert link by creating a new incident
- alert analyst note save
- incidents list
- incident detail
- incident state transition
- incident invalid-transition rejection path
- assets
- responses
- rules and policies
- policy enable/disable toggles
- analyst forbidden policy mutation path
- reports
- export trigger coverage for alerts
- export trigger coverage for incidents
- not-found empty states for unknown alert and incident detail routes (`detail-record-not-found`)
- client-side validation feedback for empty analyst note saves (`analyst-notes-feedback`)
- administrator notification panels on incident detail and on alerts linked to an incident (`incident-notifications-panel`, `alert-notifications-panel`, plus either `notification-event-row` or `notification-empty-state`)
- responses list table or filtered-empty state; optional `response-row-notification-summary` when the API includes delivery copy on list rows
- related-response notification delivery subsection when the API returns `related_notifications` (`response-linked-notification-deliveries`, `response-notification-delivery-item`)
- one happy-path validation for each supported detection (`scenario-coverage.spec.ts`), including:
  - overview dashboard detection badges (all four types always listed from the API with counts)
  - alerts queue filtered by detection type
  - incidents queue filtered by detection type when the scenario produced a linked incident
  - response history table showing the scenario’s expected policy action label (`block_ip`, `create_manual_review`, or `notify_admin`, rendered with `formatTokenLabel`)
  - `brute_force`
  - `file_integrity_violation`
  - `port_scan`
  - `unauthorized_user_creation`

## Stable `data-testid` hooks (browser tests)

| Hook | Purpose |
|------|---------|
| `detail-record-not-found` | Alert/incident detail routes when the record is missing |
| `incident-notifications-panel` / `alert-notifications-panel` | Administrator notification sections on detail pages |
| `alert-notification-link-required` | Alert not linked to an incident (notifications scoped to incidents) |
| `notification-event-row` / `notification-empty-state` | Notification history rows or empty copy inside those panels |
| `alert-workflow-feedback` | Acknowledge/close/link workflow success or error message on alert detail |
| `analyst-notes-feedback` | Analyst note save validation or success copy |
| `response-linked-notification-deliveries` / `response-notification-delivery-item` | Nested delivery list on related response cards |
| `response-row-notification-summary` | Optional delivery summary line in the responses list table |

## Test Files

- `apps/web/tests/core-workflows.spec.ts`
- `apps/web/tests/scenario-coverage.spec.ts`
- `apps/web/tests/write-workflows.spec.ts`
- `apps/web/tests/notification-and-negative-paths.spec.ts`
- `apps/web/tests/support/e2e.ts`

## Runbook

Playwright starts the Vite dev server and proxies `/api` to **`http://127.0.0.1:8000`**. Start the API (for example `docker compose up -d api`), apply migrations if needed, and seed users so login succeeds:

```powershell
docker compose exec api python -m app.db.seed
npm run test:web:e2e
```

### Latest recorded run (release candidate, 2026-04-08)

- **16 passed**, **0 skipped** against a Compose-backed API with a seeded database.

### Conditional skips (honest branch coverage)

In **other** environments (empty DB, missing incidents, or no alerts linked to incidents), the following may skip or narrow assertions:

- `notification-and-negative-paths.spec.ts` — combined notification/responses test skips when no incident exists or no alert has an incident link.
- `write-workflows.spec.ts` — incident transition, policy toggle, export, and invalid-transition tests skip when no non-terminal incident candidate exists after seeding.

These branches are **data-dependent**, not flaky styling tests; a healthy seeded lab run should execute them (as in the latest RC pass).

## Remaining Gaps

- There is no dedicated response **detail** route in the UI; notification delivery lines on the responses **list** are asserted only when the backend populates `notificationSummary` on list rows.
- Linked-alert **Related responses** notification sublists (`response-linked-notification-deliveries`) are not separately asserted in Playwright when no execution in the fixture set includes `related_notifications`.
- Reports export coverage validates browser download triggers, not full file-content parsing in browser assertions.
- Browser coverage validates one analyst forbidden mutation path (`PATCH /policies/{id}`), but does not yet exhaustively cover every role-protected endpoint negative path.
- Incident transition negative coverage validates one deterministic invalid-action rejection path, not every invalid-state/action permutation.
- Incident-state-transition and policy/export mutation checks are executed when at least one incident candidate is available; the spec skips those branches when the seeded run produces no incident records.
- Coverage is intentionally practical and SME-oriented; it is not a pixel-test suite and it avoids brittle styling assertions.

## Future Coverage Work

- extend analyst-role browser checks to manual-ingestion route surfaces and other admin-only mutations where UI exposure exists
- add additional invalid transition matrix checks if workflow complexity increases
- add targeted export file-content validation in API-layer tests for generated CSV/JSON payload integrity
