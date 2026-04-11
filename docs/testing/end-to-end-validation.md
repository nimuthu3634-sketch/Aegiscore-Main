# AegisCore End-to-End Validation

**Final product:** **AegisCore** is the **centralized SOC platform MVP** under test (**single-tenant**). Definition: **[final-product.md](../final-product.md)**.

This document validates that **transparent MVP** posture. The **current academic release** is intentionally limited to the **four validated threat categories**:

- `brute_force`
- `port_scan`
- `file_integrity_violation`
- `unauthorized_user_creation`

The goal of this validation pass is to prove the real application flow works end to end for those scenarios only:

1. source event ingestion
2. normalization into the AegisCore alert schema
3. risk scoring
4. incident creation or grouping
5. automated response policy execution
6. report visibility
7. frontend visibility across the live SOC workflows

## Validation Methods

Backend and live-lab validation used these commands:

```powershell
docker compose run --rm --entrypoint pytest api
py -3 scripts/validate_attack_scenarios.py
```

Frontend validation used these commands:

```powershell
npm run lint:web
npm run build:web
npm run test:web:e2e
```

The live-lab validation script uses the real authenticated API, ingests the supported Wazuh and Suricata fixtures, then verifies alert detail, incident detail, and daily reporting output. It also mutates each fixture external identifier per run so duplicate suppression does not hide regressions.

## Scenario Matrix

| Scenario | Source fixture | Ingestion | Normalization check | Score result | Incident behavior | Automated response | Reports | UI visibility |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `brute_force` | Wazuh fixture | Confirmed through `/integrations/wazuh/events` | `failed_attempts=24` | High/critical scoring confirmed in live runs | Incident created and linked | Response history shows policy-driven action for the alert/incident | Included in daily summary and exports | Covered in alert detail, incident detail, and reports UI |
| `file_integrity_violation` | Wazuh fixture | Confirmed through `/integrations/wazuh/events` | `file_path=D:\Operations\Policies\access-control.xlsx` | High risk with explanation drivers present | Incident created and linked | Response history reflects manual-review style policy outcome | Included in daily summary and exports | Covered in alert detail and reports UI |
| `port_scan` | Suricata fixture | Confirmed through `/integrations/suricata/events` | `destination_port=3389` | High risk scoring confirmed | Incident now auto-created when incident-level policies match | Response history shows incident-policy execution after alert scoring | Included in daily summary and exports | Covered in alert detail, incident detail, and reports UI |
| `unauthorized_user_creation` | Wazuh fixture | Confirmed through `/integrations/wazuh/events` | `username=unknown-admin` | Critical scoring confirmed | Incident created and linked | Response history shows admin-notification style policy outcome | Included in daily summary and exports | Covered in alert detail, incident detail, and reports UI |

## Latest Live Validation Snapshot

The latest successful run of `py -3 scripts/validate_attack_scenarios.py` (**2026-04-08**, release-candidate verification) returned:

| Scenario | Ingestion | Alert | Incident | Risk | Responses | Daily report alerts |
| --- | --- | --- | --- | ---: | ---: | ---: |
| `brute_force` | `ingested` | `d7b07955-a0ef-423d-8f2e-74be432c33ff` | `12e79f3c-f5b6-4156-a109-cd0803fb4e99` | 100 | 1 | 152 |
| `file_integrity_violation` | `ingested` | `70d1c7f9-8b76-424d-a00d-84c971a7134e` | `9134f42e-9a75-4ff9-a079-53fb44724512` | 100 | 1 | 145 |
| `port_scan` | `ingested` | `ce5dfb1f-9e1f-4d72-9b11-2b07ad489470` | `16f321d9-897e-44da-b389-74c19376b3f2` | 100 | 1 | 145 |
| `unauthorized_user_creation` | `ingested` | `25d5880f-e8f1-49a7-ac54-3b9cfc479bc2` | `b2916743-dab1-4c35-b5a9-7c91d7501ce1` | 100 | 1 | 144 |

Daily report totals reflect **all** alerts in the daily window for that API database, not only the scenario row; they are useful as a sanity check that the report API returns data, not as a fixed regression count.

## Validation Notes

- The dashboard summary’s `alerts_by_detection` list always includes **all four** validated threat categories (count `0` when none are ingested), so lab UIs treat every approved scenario symmetrically.
- The ingestion pipeline preserves raw payloads and rejects unsupported detections explicitly.
- Asset resolution was hardened during this validation cycle to safely reuse an existing asset when a duplicate hostname create race occurs.
- `port_scan` now validates cleanly end to end because incident-scoped automated-response policies can create the minimal incident context they require after scoring.
- The validation intentionally does not cover unsupported detections or enterprise SOAR behaviors.

## Honest Remaining Gaps

- Live connector support exists for Wazuh and Suricata, but deterministic validation in this document still uses fixture-backed ingestion as the default repeatable proof path.
- Browser coverage includes major write workflows, selected negative paths, and notification panel surfaces (see [playwright-coverage.md](playwright-coverage.md)); it does not cover every negative-path role restriction or terminal edge case.
- Daily summary visibility is confirmed for the four validated threat categories, but there is no scheduled or emailed reporting workflow yet.

## Future Validation Work

- add browser checks for analyst-restricted mutation paths and selected terminal-state transitions
- add fixture-backed regression cases for retry-heavy malformed ingestion sequences
- extend connector-compatibility validation against additional live Wazuh API envelope variants and Suricata forwarding modes
