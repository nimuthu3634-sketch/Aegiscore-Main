from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import hash_password
from app.models.asset import Asset
from app.models.audit_log import AuditLog
from app.models.enums import (
    AlertStatus,
    AssetCriticality,
    DetectionType,
    IncidentPriority,
    IncidentStatus,
    ResponseMode,
    ResponseStatus,
    RoleName,
)
from app.models.incident import Incident
from app.models.normalized_alert import NormalizedAlert
from app.models.raw_alert import RawAlert
from app.models.response_action import ResponseAction
from app.models.risk_score import RiskScore
from app.models.role import Role
from app.models.user import User
from app.repositories.assets import AssetsRepository
from app.repositories.audit_logs import AuditLogsRepository
from app.repositories.incidents import IncidentsRepository
from app.repositories.responses import ResponsesRepository
from app.repositories.roles import RolesRepository
from app.repositories.users import UsersRepository


def seed_database(session: Session) -> None:
    settings = get_settings()
    roles_repository = RolesRepository(session)
    users_repository = UsersRepository(session)

    admin_role = roles_repository.get_by_name(RoleName.ADMIN)
    if admin_role is None:
        admin_role = roles_repository.create(
            Role(
                name=RoleName.ADMIN,
                description="Full access to the AegisCore SME SOC workspace.",
            )
        )

    analyst_role = roles_repository.get_by_name(RoleName.ANALYST)
    if analyst_role is None:
        analyst_role = roles_repository.create(
            Role(
                name=RoleName.ANALYST,
                description="Investigation and response access for analysts.",
            )
        )

    admin_user = users_repository.get_by_username(settings.dev_seed_admin_username)
    if admin_user is None:
        admin_user = users_repository.create(
            User(
                role=admin_role,
                username=settings.dev_seed_admin_username,
                password_hash=hash_password(settings.dev_seed_admin_password),
                full_name="AegisCore Administrator",
                is_active=True,
            )
        )

    analyst_user = users_repository.get_by_username(settings.dev_seed_analyst_username)
    if analyst_user is None:
        analyst_user = users_repository.create(
            User(
                role=analyst_role,
                username=settings.dev_seed_analyst_username,
                password_hash=hash_password(settings.dev_seed_analyst_password),
                full_name="AegisCore Analyst",
                is_active=True,
            )
        )

    session.flush()

    assets_repository = AssetsRepository(session)
    if assets_repository.list_assets():
        session.commit()
        return

    primary_assets = [
        Asset(
            hostname="acct-web-01",
            ip_address="10.20.1.15",
            operating_system="Ubuntu 22.04 LTS",
            criticality=AssetCriticality.HIGH,
        ),
        Asset(
            hostname="acct-db-01",
            ip_address="10.20.1.20",
            operating_system="PostgreSQL Appliance",
            criticality=AssetCriticality.CRITICAL,
        ),
        Asset(
            hostname="acct-windows-01",
            ip_address="10.20.1.35",
            operating_system="Windows Server 2022",
            criticality=AssetCriticality.MEDIUM,
        ),
    ]
    for asset in primary_assets:
        assets_repository.create(asset)

    session.flush()
    now = datetime.now(UTC)

    seeded_pairs: list[tuple[RawAlert, NormalizedAlert, RiskScore]] = [
        (
            RawAlert(
                asset=primary_assets[2],
                source="wazuh",
                external_id="wazuh-1001",
                detection_type=DetectionType.UNAUTHORIZED_USER_CREATION,
                severity=9,
                raw_payload={
                    "rule_id": 60115,
                    "agent": "acct-windows-01",
                    "new_user": "svc-shadow",
                },
                received_at=now - timedelta(minutes=38),
            ),
            NormalizedAlert(
                asset=primary_assets[2],
                source="wazuh",
                title="Unauthorized user creation detected",
                description="A privileged local account was created outside approved change windows.",
                detection_type=DetectionType.UNAUTHORIZED_USER_CREATION,
                severity=9,
                status=AlertStatus.INVESTIGATING,
                normalized_payload={
                    "username": "svc-shadow",
                    "asset_hostname": "acct-windows-01",
                    "source": "wazuh",
                },
                created_at=now - timedelta(minutes=37),
            ),
            RiskScore(
                score=0.96,
                confidence=0.92,
                reasoning="High-confidence admin account creation on a monitored server.",
                calculated_at=now - timedelta(minutes=36),
            ),
        ),
        (
            RawAlert(
                asset=primary_assets[0],
                source="suricata",
                external_id="suricata-2048",
                detection_type=DetectionType.PORT_SCAN,
                severity=6,
                raw_payload={
                    "signature": "ET SCAN Potential SSH Scan",
                    "src_ip": "198.51.100.22",
                    "dest_ip": "10.20.1.15",
                },
                received_at=now - timedelta(minutes=31),
            ),
            NormalizedAlert(
                asset=primary_assets[0],
                source="suricata",
                title="External port scan observed",
                description="Repeated TCP connection attempts targeted the web tier across multiple ports.",
                detection_type=DetectionType.PORT_SCAN,
                severity=6,
                status=AlertStatus.NEW,
                normalized_payload={
                    "scanner_ip": "198.51.100.22",
                    "target_hostname": "acct-web-01",
                    "target_ports": [22, 80, 443],
                },
                created_at=now - timedelta(minutes=30),
            ),
            RiskScore(
                score=0.54,
                confidence=0.73,
                reasoning="External reconnaissance detected against an internet-facing asset.",
                calculated_at=now - timedelta(minutes=29),
            ),
        ),
        (
            RawAlert(
                asset=primary_assets[1],
                source="wazuh",
                external_id="wazuh-8421",
                detection_type=DetectionType.FILE_INTEGRITY_VIOLATION,
                severity=8,
                raw_payload={
                    "file_path": "/etc/nginx/nginx.conf",
                    "change_type": "modified",
                },
                received_at=now - timedelta(minutes=26),
            ),
            NormalizedAlert(
                asset=primary_assets[1],
                source="wazuh",
                title="Protected configuration file changed",
                description="A monitored infrastructure config changed outside the approved deployment path.",
                detection_type=DetectionType.FILE_INTEGRITY_VIOLATION,
                severity=8,
                status=AlertStatus.INVESTIGATING,
                normalized_payload={
                    "file_path": "/etc/nginx/nginx.conf",
                    "asset_hostname": "acct-db-01",
                },
                created_at=now - timedelta(minutes=25),
            ),
            RiskScore(
                score=0.88,
                confidence=0.89,
                reasoning="Integrity change affected a critical configuration path.",
                calculated_at=now - timedelta(minutes=24),
            ),
        ),
        (
            RawAlert(
                asset=primary_assets[0],
                source="wazuh",
                external_id="wazuh-9217",
                detection_type=DetectionType.BRUTE_FORCE,
                severity=7,
                raw_payload={
                    "service": "ssh",
                    "failed_attempts": 23,
                    "src_ip": "203.0.113.44",
                },
                received_at=now - timedelta(minutes=18),
            ),
            NormalizedAlert(
                asset=primary_assets[0],
                source="wazuh",
                title="Repeated authentication failures detected",
                description="SSH authentication failures exceeded the brute-force threshold for the web server.",
                detection_type=DetectionType.BRUTE_FORCE,
                severity=7,
                status=AlertStatus.NEW,
                normalized_payload={
                    "service": "ssh",
                    "failed_attempts": 23,
                    "source_ip": "203.0.113.44",
                },
                created_at=now - timedelta(minutes=17),
            ),
            RiskScore(
                score=0.78,
                confidence=0.84,
                reasoning="Brute-force activity targeted a high-value internet-facing system.",
                calculated_at=now - timedelta(minutes=16),
            ),
        ),
    ]

    created_incidents: list[Incident] = []

    for raw_alert, normalized_alert, risk_score in seeded_pairs:
        raw_alert.normalized_alert = normalized_alert
        normalized_alert.risk_score = risk_score
        session.add(raw_alert)
        session.add(normalized_alert)
        session.add(risk_score)

    session.flush()

    incidents_repository = IncidentsRepository(session)
    responses_repository = ResponsesRepository(session)
    audit_logs_repository = AuditLogsRepository(session)

    active_alerts = [pair[1] for pair in seeded_pairs]
    incident_specs = [
        {
            "primary_alert": active_alerts[3],
            "linked_alerts": [active_alerts[3], active_alerts[1]],
            "assignee": admin_user,
            "status": IncidentStatus.TRIAGED,
            "priority": IncidentPriority.HIGH,
            "title": "External reconnaissance against web edge",
            "summary": (
                "Port-scan and brute-force activity are being tracked together on the "
                "internet-facing web asset."
            ),
        },
        {
            "primary_alert": active_alerts[2],
            "linked_alerts": [active_alerts[2]],
            "assignee": analyst_user,
            "status": IncidentStatus.INVESTIGATING,
            "priority": IncidentPriority.HIGH,
            "title": active_alerts[2].title,
            "summary": (
                "Configuration drift on a critical system is under active investigation."
            ),
        },
    ]

    for incident_spec in incident_specs:
        primary_alert = incident_spec["primary_alert"]
        incident = incidents_repository.create(
            Incident(
                assigned_user=incident_spec["assignee"],
                title=incident_spec["title"],
                summary=incident_spec["summary"],
                status=incident_spec["status"],
                priority=incident_spec["priority"],
                created_at=primary_alert.created_at + timedelta(minutes=1),
                updated_at=now - timedelta(minutes=5),
            )
        )
        session.flush()
        for linked_alert in incident_spec["linked_alerts"]:
            linked_alert.incident = incident
        incident.primary_alert = primary_alert
        created_incidents.append(incident)

    session.flush()

    response_actions = [
        ResponseAction(
            incident=created_incidents[0],
            requested_by=admin_user,
            action_type="disable_user_account",
            status=ResponseStatus.COMPLETED,
            mode=ResponseMode.LIVE,
            details={"username": "svc-shadow", "result": "disabled"},
            created_at=now - timedelta(minutes=15),
            executed_at=now - timedelta(minutes=14),
        ),
        ResponseAction(
            incident=created_incidents[1],
            requested_by=analyst_user,
            action_type="collect_configuration_backup",
            status=ResponseStatus.IN_PROGRESS,
            mode=ResponseMode.DRY_RUN,
            details={"path": "/etc/nginx/nginx.conf", "result": "snapshot_requested"},
            created_at=now - timedelta(minutes=10),
            executed_at=None,
        ),
    ]
    for response_action in response_actions:
        responses_repository.create(response_action)

    audit_logs = [
        AuditLog(
            actor=admin_user,
            entity_type="incident",
            entity_id=str(created_incidents[0].id),
            action="incident.created",
            details={
                "priority": created_incidents[0].priority.value,
                "primary_alert_id": str(active_alerts[3].id),
                "linked_alerts_count": 2,
            },
            created_at=now - timedelta(minutes=14),
        ),
        AuditLog(
            actor=admin_user,
            entity_type="incident",
            entity_id=str(created_incidents[0].id),
            action="incident.alert_linked",
            details={
                "alert_id": str(active_alerts[1].id),
                "link_mode": "seed",
                "linked_alerts_count": 2,
            },
            created_at=now - timedelta(minutes=13),
        ),
        AuditLog(
            actor=admin_user,
            entity_type="incident",
            entity_id=str(created_incidents[0].id),
            action="response.executed",
            details={"response_action": "disable_user_account"},
            created_at=now - timedelta(minutes=13),
        ),
        AuditLog(
            actor=analyst_user,
            entity_type="incident",
            entity_id=str(created_incidents[1].id),
            action="incident.assigned",
            details={"assigned_to": analyst_user.username},
            created_at=now - timedelta(minutes=9),
        ),
    ]
    for audit_log in audit_logs:
        audit_logs_repository.create(audit_log)

    session.commit()
