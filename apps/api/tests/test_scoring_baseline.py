from datetime import UTC, datetime

from app.models.enums import IncidentPriority
from app.services.scoring.baseline import (
    incident_priority_from_three_class_tier,
    priority_from_score,
    score_with_baseline,
)
from app.services.scoring.types import AlertRiskFeatures


def test_incident_priority_from_three_class_tier_never_critical() -> None:
    assert incident_priority_from_three_class_tier("low") == IncidentPriority.LOW
    assert incident_priority_from_three_class_tier("medium") == IncidentPriority.MEDIUM
    assert incident_priority_from_three_class_tier("high") == IncidentPriority.HIGH
    assert incident_priority_from_three_class_tier("unknown-tier") == IncidentPriority.LOW


def test_priority_from_score_thresholds() -> None:
    assert priority_from_score(91) == IncidentPriority.CRITICAL
    assert priority_from_score(74) == IncidentPriority.HIGH
    assert priority_from_score(52) == IncidentPriority.MEDIUM
    assert priority_from_score(18) == IncidentPriority.LOW


def test_score_with_baseline_returns_explainable_critical_score() -> None:
    features = AlertRiskFeatures(
        observed_at=datetime.now(UTC),
        source_type="wazuh",
        detection_type="unauthorized_user_creation",
        source_severity=9,
        source_rule_level=10,
        repeated_event_count=3,
        time_window_density=2,
        asset_criticality="critical",
        privileged_account_flag=True,
        sensitive_file_flag=False,
        repeated_source_ip=2,
        repeated_failed_logins=0,
        recurrence_history=2,
        destination_port=0,
        has_destination_port=False,
        username="svc-shadow",
        asset_hostname="acct-windows-01",
    )

    result = score_with_baseline(features, baseline_version="baseline_v1")

    assert result.score >= 85
    assert result.priority_label == IncidentPriority.CRITICAL
    assert result.baseline_version == "baseline_v1"
    assert result.explanation["scoring_method"] == "baseline_rules"
    assert result.explanation["drivers"]
