# Analyst Guide

## Purpose

This guide is for analysts using the AegisCore SOC console in a local SME or lab deployment.

## Sign In

Open `http://localhost` and sign in through the AegisCore login screen.

Default local users:

- `admin / AegisCore123!`
- `analyst / AegisCore123!`

Role expectation for this guide: analyst-level workflow. If you sign in as `admin`, the same analyst surfaces are available plus policy/ingestion administration capabilities.

## Overview Dashboard

Use the overview screen to answer four quick questions:

1. how many alerts need attention now
2. how many incidents are open
3. whether high-risk activity is clustering
4. whether recent responses succeeded or need follow-up

The dashboard is decision-oriented and backed by live backend data, not decorative mock summaries.

## Alerts Workflow

The Alerts page is the main triage queue.

- filter by severity, status, detection type, source type, asset, and date range
- sort by timestamp, severity, or risk score
- open alert detail to review normalized evidence, raw payloads, score explanation, notes, and related responses
- use alert actions to acknowledge, close, link to an existing incident, or create a new incident

## Incident Workflow

The Incidents page groups linked alerts into an investigation record.

- review linked alerts, timeline activity, affected assets, and response history
- transition the incident through `new`, `triaged`, `investigating`, `contained`, `resolved`, or `false_positive`
- use notes to preserve analyst context across refreshes

## Assets, Responses, Rules, And Reports

- Assets: review monitored endpoints, agent posture, recent alerts, and open-incident exposure
- Responses: review dry-run or live actions, execution status, and policy context
- Rules / Policies: review enabled detection-specific response policies (toggle requires `admin`)
- Reports: review daily or weekly operational summaries and export alert, incident, or response datasets

## Role Guardrails

- Analysts can triage and investigate, but cannot change response policy enabled state.
- Analysts can view connector status but cannot post manual ingestion events.
- If a restricted action is attempted with an analyst session, the API returns `403` with an explicit permission error.

## Supported Detection Scope

This build supports only:

- `brute_force`
- `file_integrity_violation`
- `port_scan`
- `unauthorized_user_creation`

If a source event does not map to one of those detections, it is out of scope for the current prototype and should not be treated as validated product coverage.

## Practical Expectations

- scoring is a prioritization aid after detection, not a replacement for analyst judgment
- automated response remains conservative and auditable
- raw payloads are preserved for debugging, but normal investigation should begin with the normalized alert and incident views
