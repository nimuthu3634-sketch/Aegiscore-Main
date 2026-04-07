# AegisCore Requirement Compliance Matrix

This matrix maps the proposal requirement set to the current implementation and validation posture of AegisCore.

Scope note: AegisCore remains intentionally single-tenant and SME/lab-focused. It is not an enterprise commercial SOC platform.

Release-candidate note: this matrix reflects the final scoped v1 release-candidate posture, not an enterprise production-cloud claim.

| Requirement | Implementation status | Code/docs evidence | Remaining limitation (if any) |
| --- | --- | --- | --- |
| Gather and monitor logs from monitored machines | Implemented (lab-ready) | `apps/api/app/services/integrations/wazuh_connector.py`; `apps/api/app/services/ingestion/service.py`; `docs/setup/wazuh-live-integration.md` | Wazuh authenticated live polling is implemented with retries, pagination/checkpointing, dedupe, and status visibility; compatibility is focused on common Wazuh lab envelope variants. |
| Monitor network traffic | Implemented (lab-ready) | `apps/api/app/services/integrations/suricata_connector.py`; `apps/api/app/services/integrations/checkpoints.py`; `docs/setup/suricata-live-integration.md` | Live mode is `file_tail` for `eve.json` with checkpointing and retry/error behavior; authenticated forwarding mode is not yet implemented. |
| Detect only the four in-scope threats | Implemented and enforced | `apps/api/app/models/enums.py` (`DetectionType`); `apps/api/app/services/ingestion/parsers.py` (unsupported detection rejection); `AGENTS.md`; `README.md` | No gap for current scope; additional detections are intentionally out of scope. |
| Centralized dashboard | Implemented | `apps/web/src/pages/DashboardPage.tsx`; `apps/web/src/components/layout/AppShell.tsx`; `apps/api/app/api/routes/dashboard.py`; `README.md` | Dashboard remains intentionally compact and local-scope, not enterprise BI. |
| AI risk scoring | Implemented (baseline default + optional ML) | `apps/api/app/services/scoring/baseline.py`; `apps/api/app/services/scoring/ml.py`; `ai/training/train_risk_model.py`; `docs/scoring.md` | ML path depends on local model artifact availability; baseline fallback is used when model artifacts are absent. |
| Basic automated response | Implemented with safety gates | `apps/api/app/services/response_automation/execution.py`; `apps/api/app/services/response_automation/adapters.py`; `apps/api/app/services/notifications/service.py`; `docs/setup/operator-guide.md` | Destructive adapters are disabled by default and require explicit lab safety flags. |
| Incident/response recording | Implemented and auditable | `apps/api/app/models/incident.py`; `apps/api/app/models/response_action.py`; `apps/api/app/models/audit_log.py`; `apps/api/app/services/incidents.py`; `apps/api/app/services/alerts.py`; `apps/web/src/pages/IncidentDetailPage.tsx` | No major gap for current scope; historical analytics remain operational rather than long-horizon enterprise reporting. |
| VM/lab validation | Implemented and documented | `scripts/validate_attack_scenarios.py`; `docs/testing/end-to-end-validation.md`; `docs/testing/playwright-coverage.md`; `docs/release-readiness.md`; `docs/setup/operator-guide.md`; `docs/setup/operator-runbook.md` | Deterministic validation still relies heavily on fixtures even though live connectors are available; some browser branches are conditionally skipped when incident candidates are unavailable in seeded runs. |
| Practical authenticated access | Implemented (JWT + admin/analyst) | `apps/api/app/api/routes/auth.py`; `apps/api/app/api/deps.py`; `apps/web/src/pages/LoginPage.tsx`; `apps/web/src/lib/api.ts`; `apps/web/src/pages/RulesPage.tsx`; `docs/setup/analyst-guide.md` | Role model is intentionally minimal (`admin`, `analyst`) and does not include enterprise RBAC customization. |
| Honest local/lab deployment posture | Implemented in docs and runtime guardrails | `README.md`; `docs/release-readiness.md`; `docs/project-status-summary.md`; `docker-compose.yml`; `apps/api/app/api/routes/health.py` | Not positioned for enterprise production; no claim of multi-tenant/cloud orchestration maturity. |

## Reviewer Notes

- Requirement compliance is strongest for the bounded SME SOC workflow: ingestion, normalization, scoring, incident handling, basic response, and operational reporting.
- Remaining limitations are explicit, mostly connector compatibility breadth and intentionally deferred enterprise-scale features.
