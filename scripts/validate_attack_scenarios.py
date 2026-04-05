from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT_DIR = Path(__file__).resolve().parents[1]
FIXTURES_DIR = ROOT_DIR / "apps" / "api" / "tests" / "fixtures" / "ingestion"


@dataclass(frozen=True)
class ScenarioDefinition:
    key: str
    source: str
    fixture_file: str
    detection_type: str
    normalized_field: str
    expected_value: Any


SCENARIOS = [
    ScenarioDefinition(
        key="brute_force",
        source="wazuh",
        fixture_file="wazuh_brute_force.json",
        detection_type="brute_force",
        normalized_field="failed_attempts",
        expected_value=24,
    ),
    ScenarioDefinition(
        key="file_integrity_violation",
        source="wazuh",
        fixture_file="wazuh_file_integrity_violation.json",
        detection_type="file_integrity_violation",
        normalized_field="file_path",
        expected_value="D:\\Operations\\Policies\\access-control.xlsx",
    ),
    ScenarioDefinition(
        key="port_scan",
        source="suricata",
        fixture_file="suricata_port_scan.json",
        detection_type="port_scan",
        normalized_field="destination_port",
        expected_value=3389,
    ),
    ScenarioDefinition(
        key="unauthorized_user_creation",
        source="wazuh",
        fixture_file="wazuh_unauthorized_user_creation.json",
        detection_type="unauthorized_user_creation",
        normalized_field="username",
        expected_value="unknown-admin",
    ),
]


class ValidationError(RuntimeError):
    pass


def request_json(
    *,
    base_url: str,
    path: str,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
    token: str | None = None,
    query: dict[str, Any] | None = None,
) -> dict[str, Any]:
    url = f"{base_url.rstrip('/')}/{path.lstrip('/')}"
    if query:
        filtered = {
            key: value
            for key, value in query.items()
            if value not in (None, "", [])
        }
        if filtered:
            url = f"{url}?{urlencode(filtered)}"

    headers = {
        "Accept": "application/json",
    }
    body: bytes | None = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(payload).encode("utf-8")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = Request(url, method=method, headers=headers, data=body)

    try:
        with urlopen(request) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:  # pragma: no cover - error path depends on live API
        details = exc.read().decode("utf-8", errors="replace")
        raise ValidationError(
            f"{method} {url} failed with {exc.code}: {details}"
        ) from exc


def login(*, base_url: str, username: str, password: str) -> str:
    response = request_json(
        base_url=base_url,
        path="/auth/login",
        method="POST",
        payload={"username": username, "password": password},
    )
    access_token = response.get("access_token")
    if not isinstance(access_token, str) or not access_token:
        raise ValidationError("Login response did not contain an access_token.")
    return access_token


def load_fixture(name: str) -> dict[str, Any]:
    return json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))


def with_unique_external_id(
    payload: dict[str, Any],
    *,
    source: str,
    suffix: str,
) -> dict[str, Any]:
    cloned = json.loads(json.dumps(payload))

    if source == "wazuh":
        payload_id = cloned.get("id")
        if isinstance(payload_id, str):
            cloned["id"] = f"{payload_id}-{suffix}"

        data = cloned.get("data")
        if isinstance(data, dict):
            event_id = data.get("event_id")
            if isinstance(event_id, str):
                data["event_id"] = f"{event_id}-{suffix}"

    if source == "suricata":
        flow_id = cloned.get("flow_id")
        if isinstance(flow_id, str):
            cloned["flow_id"] = f"{flow_id}-{suffix}"

    return cloned


def validate_scenario(
    *,
    base_url: str,
    token: str,
    scenario: ScenarioDefinition,
) -> dict[str, Any]:
    payload = with_unique_external_id(
        load_fixture(scenario.fixture_file),
        source=scenario.source,
        suffix=uuid.uuid4().hex[:8],
    )
    ingestion_response = request_json(
        base_url=base_url,
        path=f"/integrations/{scenario.source}/events",
        method="POST",
        payload=payload,
        token=token,
    )

    alert_summary = ingestion_response.get("alert") or {}
    alert_id = alert_summary.get("id")
    if not isinstance(alert_id, str) or not alert_id:
        raise ValidationError(f"{scenario.key}: ingestion did not return an alert id.")

    alert_detail = request_json(
        base_url=base_url,
        path=f"/alerts/{alert_id}",
        token=token,
    )
    if alert_detail.get("detection_type") != scenario.detection_type:
        raise ValidationError(
            f"{scenario.key}: expected detection_type={scenario.detection_type}, "
            f"got {alert_detail.get('detection_type')!r}."
        )

    normalized_details = alert_detail.get("normalized_details") or {}
    if normalized_details.get(scenario.normalized_field) != scenario.expected_value:
        raise ValidationError(
            f"{scenario.key}: expected normalized_details[{scenario.normalized_field!r}] "
            f"to equal {scenario.expected_value!r}, got "
            f"{normalized_details.get(scenario.normalized_field)!r}."
        )

    risk_score = alert_detail.get("risk_score")
    if not isinstance(risk_score, (int, float)):
        raise ValidationError(f"{scenario.key}: alert risk score is missing.")

    if not alert_detail.get("score_explanation"):
        raise ValidationError(f"{scenario.key}: score explanation is missing.")

    linked_incident = alert_detail.get("linked_incident")
    if not isinstance(linked_incident, dict) or not linked_incident.get("id"):
        raise ValidationError(f"{scenario.key}: linked incident is missing.")

    incident_id = str(linked_incident["id"])
    incident_detail = request_json(
        base_url=base_url,
        path=f"/incidents/{incident_id}",
        token=token,
    )
    if not incident_detail.get("linked_alerts"):
        raise ValidationError(f"{scenario.key}: incident detail linked_alerts is empty.")

    if not incident_detail.get("response_history"):
        raise ValidationError(
            f"{scenario.key}: incident detail response_history is empty."
        )

    report_summary = request_json(
        base_url=base_url,
        path="/reports/daily-summary",
        token=token,
        query={"detection_type": scenario.detection_type},
    )
    if int(report_summary.get("total_alerts") or 0) < 1:
        raise ValidationError(
            f"{scenario.key}: daily report did not include any matching alerts."
        )

    return {
        "scenario": scenario.key,
        "status": ingestion_response.get("status"),
        "alert_id": alert_id,
        "incident_id": incident_id,
        "risk_score": round(float(risk_score)),
        "responses": len(alert_detail.get("related_responses") or []),
        "report_alerts": int(report_summary.get("total_alerts") or 0),
    }


def print_markdown_table(results: list[dict[str, Any]]) -> None:
    print("| Scenario | Ingestion | Alert | Incident | Risk | Responses | Daily report alerts |")
    print("| --- | --- | --- | --- | ---: | ---: | ---: |")
    for item in results:
        print(
            "| {scenario} | {status} | {alert_id} | {incident_id} | {risk_score} | {responses} | {report_alerts} |".format(
                **item
            )
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate the four supported AegisCore attack scenarios end to end against a "
            "running backend API."
        )
    )
    parser.add_argument(
        "--base-url",
        default=os.environ.get("AEGISCORE_API_BASE_URL", "http://127.0.0.1:8000"),
        help="Base URL for the backend API.",
    )
    parser.add_argument(
        "--username",
        default=os.environ.get("AEGISCORE_API_USERNAME", "admin"),
        help="Backend username for validation.",
    )
    parser.add_argument(
        "--password",
        default=os.environ.get("AEGISCORE_API_PASSWORD", "AegisCore123!"),
        help="Backend password for validation.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    token = login(base_url=args.base_url, username=args.username, password=args.password)
    results: list[dict[str, Any]] = []

    for scenario in SCENARIOS:
        results.append(
            validate_scenario(
                base_url=args.base_url,
                token=token,
                scenario=scenario,
            )
        )

    print_markdown_table(results)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValidationError as exc:
        print(f"Validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
