from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.models.enums import IncidentPriority, ScoreMethod


@dataclass(frozen=True)
class AlertRiskFeatures:
    observed_at: datetime
    source_type: str
    detection_type: str
    source_severity: int
    source_rule_level: int
    repeated_event_count: int
    time_window_density: int
    asset_criticality: str
    privileged_account_flag: bool
    sensitive_file_flag: bool
    repeated_source_ip: int
    repeated_failed_logins: int
    recurrence_history: int
    destination_port: int
    has_destination_port: bool
    source_ip: str | None = None
    destination_ip: str | None = None
    username: str | None = None
    asset_hostname: str | None = None
    asset_id: str | None = None
    alert_id: str | None = None
    external_id: str | None = None
    # TensorFlow alert_prioritization_v1 row fields (Wazuh/Suricata-derived; not model outputs).
    failed_logins_1m: int = 0
    failed_logins_5m: int = 0
    unique_ports_1m: int = 0
    integrity_change: str = "none"
    new_user_created: int = 0
    off_hours: int = 0
    blacklisted_ip: int = 0
    suricata_severity: int = 0

    def to_model_input(self) -> dict[str, Any]:
        return {
            "source_type": self.source_type,
            "detection_type": self.detection_type,
            "asset_criticality": self.asset_criticality,
            "source_severity": self.source_severity,
            "source_rule_level": self.source_rule_level,
            "repeated_event_count": self.repeated_event_count,
            "time_window_density": self.time_window_density,
            "repeated_source_ip": self.repeated_source_ip,
            "repeated_failed_logins": self.repeated_failed_logins,
            "recurrence_history": self.recurrence_history,
            "destination_port": self.destination_port,
            "has_destination_port": int(self.has_destination_port),
            "privileged_account_flag": int(self.privileged_account_flag),
            "sensitive_file_flag": int(self.sensitive_file_flag),
        }

    def to_snapshot(self) -> dict[str, Any]:
        snapshot = self.to_model_input()
        snapshot.update(
            {
                "observed_at": self.observed_at.isoformat(),
                "source_ip": self.source_ip,
                "destination_ip": self.destination_ip,
                "username": self.username,
                "asset_hostname": self.asset_hostname,
                "asset_id": self.asset_id,
                "alert_id": self.alert_id,
                "external_id": self.external_id,
                "threat_type": (
                    "file_integrity"
                    if self.detection_type == "file_integrity_violation"
                    else self.detection_type
                ),
                "failed_logins_1m": self.failed_logins_1m,
                "failed_logins_5m": self.failed_logins_5m,
                "unique_ports_1m": self.unique_ports_1m,
                "integrity_change": self.integrity_change,
                "new_user_created": self.new_user_created,
                "off_hours": self.off_hours,
                "privileged_account": int(self.privileged_account_flag),
                "wazuh_rule_level": self.source_rule_level,
                "suricata_severity": self.suricata_severity,
                "blacklisted_ip": self.blacklisted_ip,
            }
        )
        return snapshot


@dataclass(frozen=True)
class ScoreContribution:
    feature: str
    label: str
    contribution: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "feature": self.feature,
            "label": self.label,
            "contribution": self.contribution,
        }


@dataclass(frozen=True)
class ScoringResult:
    score: float
    confidence: float
    priority_label: IncidentPriority
    scoring_method: ScoreMethod
    reasoning: str
    explanation: dict[str, Any]
    feature_snapshot: dict[str, Any]
    baseline_version: str | None = None
    model_version: str | None = None
