# AegisCore Requirement Compliance Matrix

This matrix maps the proposal requirement set to the current implementation and validation posture of AegisCore.

**Product positioning:** AegisCore is the **final scoped v1 product** for this project—**single-tenant**, **SME/lab** deployment—and **not an enterprise commercial SOC platform**.

**Approved scope (this project only):** monitor system logs (Wazuh) and network traffic (Suricata); detect only **`brute_force`**, **`file_integrity_violation`**, **`port_scan`**, **`unauthorized_user_creation`**; centralized dashboard; ML-capable risk scoring (baseline default, optional trainable path); basic automated response; incident and response recording; VM/lab validation with simulated attacks.

**Explicitly out of scope:** ransomware/phishing/APT/zero-day detection products, large-scale enterprise rollout claims, and full commercial-grade SOC feature parity.

Release-candidate note: this matrix reflects that final scoped v1 posture, not an enterprise production-cloud claim.

| Requirement | Implementation status | Code/docs evidence | Remaining limitation (if any) |
| --- | --- | --- | --- |
| Gather and monitor logs from monitored machines | Implemented (lab-ready) | `apps/api/app/services/integrations/wazuh_connector.py`; `apps/api/app/services/ingestion/service.py`; `docs/setup/wazuh-live-integration.md` | Wazuh authenticated live polling is implemented with retries, pagination/checkpointing, dedupe, and status visibility; compatibility is focused on common Wazuh lab envelope variants. |
| Monitor network traffic | Implemented (lab-ready) | `apps/api/app/services/integrations/suricata_connector.py`; `apps/api/app/services/integrations/checkpoints.py`; `docs/setup/suricata-live-integration.md` | Live mode is `file_tail` for `eve.json` with checkpointing and retry/error behavior; authenticated forwarding mode is not yet implemented. |
| Detect only the four in-scope threats | Implemented and enforced | `apps/api/app/models/enums.py` (`DetectionType`); `apps/api/app/services/ingestion/parsers.py` (unsupported detection rejection); `AGENTS.md`; `README.md` | No gap for current scope; additional detections are intentionally out of scope. |
| Centralized dashboard | Implemented | `apps/web/src/pages/DashboardPage.tsx`; `apps/web/src/components/layout/AppShell.tsx`; `apps/api/app/api/routes/dashboard.py`; `README.md` | Dashboard remains intentionally compact and local-scope, not enterprise BI. |
| ML-based / AI risk scoring | Implemented (baseline default + optional trainable model) | `apps/api/app/services/scoring/baseline.py`; `apps/api/app/services/scoring/ml.py`; `ai/training/train_risk_model.py`; `docs/scoring.md` | Baseline is always available; optional scikit-learn path requires artifacts and config; not a separate “black box” product beyond scoped prioritization. |
| Basic automated response | Implemented with safety gates | `apps/api/app/services/response_automation/execution.py`; `apps/api/app/services/response_automation/adapters.py`; `apps/api/app/services/notifications/service.py`; `docs/setup/operator-guide.md` | Destructive adapters are disabled by default and require explicit lab safety flags. |
| Critical-incident / operator notifications | Implemented (log + SMTP) | `apps/api/app/services/notifications/service.py`; `apps/api/app/models/notification_event.py`; `apps/api/app/services/response_automation/execution.py` (risk + response triggers); `apps/api/app/services/incidents.py` (state transitions); `apps/web/src/pages/IncidentDetailPage.tsx`; `apps/web/src/pages/AlertDetailPage.tsx`; `docs/setup/notifications.md` | No paging/on-call integrations; scheduled digest email is not implemented (operational reporting exports remain separate). |
| Incident/response recording | Implemented and auditable | `apps/api/app/models/incident.py`; `apps/api/app/models/response_action.py`; `apps/api/app/models/audit_log.py`; `apps/api/app/services/incidents.py`; `apps/api/app/services/alerts.py`; `apps/web/src/pages/IncidentDetailPage.tsx` | No major gap for current scope; historical analytics remain operational rather than long-horizon enterprise reporting. |
| VM/lab validation (simulated attacks) | Implemented and documented | `scripts/validate_attack_scenarios.py`; `docs/testing/end-to-end-validation.md`; `docs/testing/playwright-coverage.md`; `docs/release-readiness.md`; `docs/setup/operator-guide.md`; `docs/setup/operator-runbook.md` | Repeatable proof uses fixture-driven scenarios against the real API; live connectors add optional lab checks. **2026-04-08 RC: Playwright 16 passed / 0 skipped** with seeded Compose API; sparse DBs may still hit data-dependent skips (see playwright-coverage). |
| Practical authenticated access | Implemented (JWT + admin/analyst) | `apps/api/app/api/routes/auth.py`; `apps/api/app/api/deps.py`; `apps/web/src/pages/LoginPage.tsx`; `apps/web/src/lib/api.ts`; `apps/web/src/pages/RulesPage.tsx`; `docs/setup/analyst-guide.md` | Role model is intentionally minimal (`admin`, `analyst`) and does not include enterprise RBAC customization. |
| Honest local/lab deployment posture | Implemented in docs and runtime guardrails | `README.md`; `docs/release-readiness.md`; `docs/project-status-summary.md`; `docker-compose.yml`; `apps/api/app/api/routes/health.py` | Not positioned for enterprise production; no claim of multi-tenant/cloud orchestration maturity. |

## Reviewer Notes

- Requirement compliance is strongest for the bounded SME SOC workflow: ingestion, normalization, scoring, incident handling, basic response, and operational reporting.
- Remaining limitations are explicit, mostly connector compatibility breadth and intentionally deferred enterprise-scale features.
