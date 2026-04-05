# AegisCore End-to-End Validation

This validation scope is intentionally limited to the four supported AegisCore detections:

- `brute_force`
- `file_integrity_violation`
- `port_scan`
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
docker compose run --rm --no-deps api pytest
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

The latest successful run of `py -3 scripts/validate_attack_scenarios.py` returned:

| Scenario | Ingestion | Alert | Incident | Risk | Responses | Daily report alerts |
| --- | --- | --- | --- | ---: | ---: | ---: |
| `brute_force` | `ingested` | `bdee1b18-ce8a-4611-8f2f-3b1bf86cb795` | `c967d9ce-ab5d-40e0-885b-7a212095df75` | 100 | 1 | 5 |
| `file_integrity_violation` | `ingested` | `baf31637-3892-4883-bbc3-1b86f890b357` | `076547e5-1879-4caa-8c0a-2c0a49987fd8` | 89 | 1 | 3 |
| `port_scan` | `ingested` | `155434c4-2230-467f-8398-68087ed4c5a0` | `ff18b43f-33c0-434e-bc73-3c9da6ad31db` | 96 | 1 | 4 |
| `unauthorized_user_creation` | `ingested` | `ff13a8d9-fe9f-4749-8b59-36bb623bb482` | `d67ffb1d-2a69-40a2-8561-ebae934b9e05` | 100 | 1 | 3 |

## Validation Notes

- The ingestion pipeline now preserves raw payloads and rejects unsupported detections explicitly.
- Asset resolution was hardened during this validation cycle to safely reuse an existing asset when a duplicate hostname create race occurs.
- `port_scan` now validates cleanly end to end because incident-scoped automated-response policies can create the minimal incident context they require after scoring.
- The validation intentionally does not cover unsupported detections or enterprise SOAR behaviors.

## Honest Remaining Gaps

- Live upstream connector auth and polling are still separate future work. This validation uses the real backend ingestion endpoints with fixture-backed Wazuh and Suricata payloads.
- Browser coverage focuses on core operational navigation, read visibility, reports, and scenario evidence. It does not yet cover every write workflow such as notes, state transitions, and policy editing in Playwright.
- Daily summary visibility is confirmed for the supported detections, but there is no scheduled or emailed reporting workflow yet.
