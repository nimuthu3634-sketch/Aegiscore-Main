# AegisCore Viva Q&A

## 1-Minute Positioning

AegisCore is the **final scoped v1 product** for this project: **single-tenant**, **SME/lab**, **not an enterprise commercial SOC platform**. It monitors **logs** (Wazuh) and **network traffic** (Suricata), detects only **`brute_force`**, **`file_integrity_violation`**, **`port_scan`**, and **`unauthorized_user_creation`**, provides a **centralized dashboard**, **ML-capable risk scores** (baseline + optional model), **basic automated response**, and full **incident/response recording**, validated in VM/lab with **simulated attacks**. It does not claim ransomware/phishing/APT/zero-day coverage or large-scale enterprise SOC features.

## Concise Viva Defense

### What The System Does

- event ingestion from Wazuh and Suricata
- normalized alert lifecycle and investigation workflow
- risk scoring with explainable baseline logic (optional ML path available)
- incident tracking, timeline, notes, audit evidence
- policy-driven response execution with persisted outcome history
- practical reporting and export for local operations

### What Is Complete

- end-to-end scoped workflow is implemented for all four supported detections
- backend role-based protection for sensitive actions is in place
- frontend reflects role constraints (for example, read-only analyst policy controls)
- deterministic test and validation commands are documented and repeatable

### What Is Still Limited

- Suricata live connector currently uses `file_tail` mode for `eve.json`
- Wazuh live compatibility is designed around common lab envelope variants
- deterministic acceptance validation remains primarily fixture-backed
- destructive live adapter behavior is intentionally gated and disabled by default

### Why It Is Still A Valid Final Scoped Product

The core SOC pipeline is fully implemented and demonstrable within declared scope: ingest -> normalize -> score -> incident -> response -> report. Remaining items are explicitly documented boundary limits rather than missing core product flow.

## Likely Examiner Questions (Top 10)

1. **Why do you call this a product and not just a prototype?**  
   It is positioned as the **final scoped v1 product** for this project: persistent data model, real APIs, role enforcement, operational docs, and repeatable validation—including VM/lab simulated-attack scenarios. The boundary is narrow (four detections, SME/lab), but the pipeline is implemented end-to-end, not a mock-up.

2. **Why only four detections?**  
   The project intentionally enforces a bounded threat scope (`brute_force`, `file_integrity_violation`, `port_scan`, `unauthorized_user_creation`) to stay defensible, testable, and aligned with stated requirements.

3. **How is AI used in the system?**  
   AI/risk scoring is used for prioritization after detection. Baseline scoring is always available; optional ML scoring is supported when model artifacts are present.

4. **How does automated response work safely?**  
   Responses are policy-driven, auditable, and split between dry-run/live modes. Destructive live actions require explicit flags, so they are not enabled by default.

5. **What proves this is not frontend-only simulation?**  
   Flows run through real backend APIs, persisted database records, and testable routes. Fixture-backed validation still executes the real ingestion and workflow pipeline.

6. **What are the major current limitations?**  
   Suricata authenticated forwarding is not implemented, Wazuh compatibility is tuned for common envelopes, deterministic validation is fixture-first, and enterprise orchestration features are out of scope.

7. **Why is this suitable for SMEs?**  
   It focuses on practical SOC essentials (triage, incidenting, safe automation, reporting) without enterprise complexity, making operation feasible in local/lab SME contexts.

8. **How are roles enforced?**  
   Backend JWT role checks are authoritative (`admin` and `analyst`). Sensitive mutations (policy updates, manual ingestion) are admin-only; frontend mirrors this with role-aware controls.

9. **If live connectors fail during demo, what is the fallback?**  
   Run `py -3 scripts/validate_attack_scenarios.py` and continue with fixture-backed deterministic flow, while clearly stating connectors are implemented but unavailable in that runtime.

10. **What would be the next logical improvements after submission?**  
    Expand Suricata ingestion modes, broaden Wazuh compatibility profiles, add deeper negative-path browser coverage, and improve replay handling for ingestion failures.

## Quick Reference Commands

```powershell
docker compose up --build -d
docker compose exec api alembic upgrade head
docker compose exec api python -m app.db.seed
docker compose run --rm --entrypoint pytest api
npm run lint:web
npm run build:web
npm run test:web:e2e
py -3 scripts/validate_attack_scenarios.py
```

## Companion Docs

- [demo-script.md](demo-script.md)
- [project-status-summary.md](project-status-summary.md)
- [release-readiness.md](release-readiness.md)
- [requirement-compliance-matrix.md](requirement-compliance-matrix.md)
