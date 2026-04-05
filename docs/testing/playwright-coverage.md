# Playwright Coverage

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
- overview dashboard
- alerts list
- alert detail
- incidents list
- incident detail
- assets
- responses
- rules and policies
- reports
- export trigger coverage for alerts
- one happy-path validation for each supported detection:
  - `brute_force`
  - `file_integrity_violation`
  - `port_scan`
  - `unauthorized_user_creation`

## Test Files

- `apps/web/tests/core-workflows.spec.ts`
- `apps/web/tests/scenario-coverage.spec.ts`
- `apps/web/tests/support/e2e.ts`

## Runbook

Start the backend stack first so the frontend dev server can proxy `/api` calls correctly, then run:

```powershell
npm run test:web:e2e
```

The latest successful run completed with `7 passed`.

## Remaining Gaps

- The suite does not yet exercise every mutation path such as analyst notes, alert close, incident transitions, or policy toggles.
- Reports export coverage validates the browser download trigger, not full file-content parsing in the browser layer.
- Coverage is intentionally practical and SME-oriented; it is not a pixel-test suite and it avoids brittle styling assertions.

## Future Coverage Work

- add browser coverage for alert acknowledge or close flows
- add browser coverage for incident transitions and note persistence
- add policy-toggle mutation coverage once those flows are stable enough for resilient browser assertions
