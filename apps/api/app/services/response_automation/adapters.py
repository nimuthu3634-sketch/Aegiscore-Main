from __future__ import annotations

import ipaddress
import json
import os
import re
import subprocess
from datetime import UTC, datetime
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.containment_flag import ContainmentFlag
from app.models.incident import Incident
from app.core.config import Settings
from app.models.enums import ResponseActionType, ResponseMode, ResponseStatus
from app.services.notifications.service import send_admin_notification
from app.services.response_automation.types import AdapterExecutionResult


@dataclass(frozen=True)
class AdapterContext:
    session: Session
    action_type: ResponseActionType
    mode: ResponseMode
    target_value: str | None
    policy_name: str
    payload: dict


def _run_script(script_path: str, payload: dict) -> tuple[int, str, str]:
    process = subprocess.run(
        [script_path],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=30,
        env=os.environ.copy(),
        check=False,
    )
    return process.returncode, process.stdout.strip(), process.stderr.strip()


def _run_command(command: list[str]) -> tuple[int, str, str]:
    process = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=30,
        env=os.environ.copy(),
        check=False,
    )
    return process.returncode, process.stdout.strip(), process.stderr.strip()


def _append_json_line(path: str, payload: dict) -> None:
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, default=str))
        handle.write("\n")


def _with_contract_details(
    *,
    action_name: str,
    preconditions: list[str],
    mode_requirements: list[str],
    extra: dict | None = None,
) -> dict:
    return {
        **(extra or {}),
        "adapter_contract": {
            "action": action_name,
            "preconditions": preconditions,
            "mode_requirements": mode_requirements,
        },
    }


def _incident_uuid_from_payload(payload: dict) -> UUID | None:
    incident_payload = payload.get("incident")
    if not isinstance(incident_payload, dict):
        return None
    raw_id = incident_payload.get("id")
    if not raw_id:
        return None
    try:
        return UUID(str(raw_id))
    except ValueError:
        return None


def _create_incident_audit(
    context: AdapterContext,
    *,
    action: str,
    details: dict,
) -> None:
    incident_id = _incident_uuid_from_payload(context.payload)
    if incident_id is None:
        return
    context.session.add(
        AuditLog(
            actor=None,
            entity_type="incident",
            entity_id=str(incident_id),
            action=action,
            details=details,
        )
    )


def _dry_run_result(context: AdapterContext) -> AdapterExecutionResult:
    target_value = context.target_value or "no target resolved"
    return AdapterExecutionResult(
        status=ResponseStatus.COMPLETED,
        summary=f"Dry-run: would execute {context.action_type.value} against {target_value}.",
        message=(
            f"Policy {context.policy_name} matched and AegisCore simulated "
            f"{context.action_type.value} in dry-run mode."
        ),
        details={
            "simulated": True,
            "mode": "dry_run",
        },
    )


def _completed_result(
    context: AdapterContext,
    *,
    summary: str,
    message: str,
    extra: dict | None = None,
) -> AdapterExecutionResult:
    return AdapterExecutionResult(
        status=ResponseStatus.COMPLETED,
        summary=summary,
        message=message,
        details=extra or {},
    )


def _validate_ip_target(target_value: str | None) -> tuple[bool, str]:
    if not target_value:
        return False, "No source IP target was resolved."
    try:
        ipaddress.ip_address(target_value)
    except ValueError:
        return False, f"Target '{target_value}' is not a valid IP address."
    return True, ""


def _validate_username_target(target_value: str | None) -> tuple[bool, str]:
    if not target_value:
        return False, "No username target was resolved."
    if not re.fullmatch(r"[a-z_][a-z0-9_-]{0,31}", target_value):
        return False, f"Target '{target_value}' is not a safe Linux username."
    return True, ""


def _warning_result(summary: str, message: str, *, extra: dict | None = None) -> AdapterExecutionResult:
    return AdapterExecutionResult(
        status=ResponseStatus.WARNING,
        summary=summary,
        message=message,
        details=extra or {},
    )


def _failed_result(summary: str, message: str, *, extra: dict | None = None) -> AdapterExecutionResult:
    return AdapterExecutionResult(
        status=ResponseStatus.FAILED,
        summary=summary,
        message=message,
        details=extra or {},
    )


def _lab_live_guard(
    context: AdapterContext,
    *,
    settings: Settings,
    action_name: str,
) -> AdapterExecutionResult | None:
    if context.mode == ResponseMode.DRY_RUN:
        return _dry_run_result(context)
    if not settings.automated_response_builtin_adapters_enabled:
        return _warning_result(
            summary=f"Built-in {action_name} adapter disabled by configuration.",
            message=(
                "AegisCore skipped live built-in adapter execution because "
                "AUTOMATED_RESPONSE_BUILTIN_ADAPTERS_ENABLED is false."
            ),
            extra={"builtin_adapters_enabled": False},
        )
    if not settings.automated_response_lab_adapters_enabled:
        return _warning_result(
            summary=f"Live {action_name} blocked because lab adapters are disabled.",
            message=(
                "Enable AUTOMATED_RESPONSE_LAB_ADAPTERS_ENABLED=true to allow "
                "live lab-safe adapter execution."
            ),
            extra={"lab_adapters_enabled": False},
        )
    return None


def _destructive_guard(action_name: str, *, settings: Settings) -> AdapterExecutionResult | None:
    if settings.automated_response_allow_destructive:
        return None
    return _warning_result(
        summary=f"Live {action_name} blocked by safety settings.",
        message=(
            "AegisCore prevented destructive live execution because "
            "AUTOMATED_RESPONSE_ALLOW_DESTRUCTIVE is disabled."
        ),
        extra={"blocked_by_safety": True},
    )


def _execute_block_ip(context: AdapterContext, *, settings: Settings) -> AdapterExecutionResult:
    preconditions = [
        "Resolved target_value must be a valid IPv4 or IPv6 address.",
    ]
    mode_requirements = [
        "Policy mode must be live for non-simulated execution.",
        "AUTOMATED_RESPONSE_BUILTIN_ADAPTERS_ENABLED=true.",
        "AUTOMATED_RESPONSE_LAB_ADAPTERS_ENABLED=true.",
    ]
    guarded = _lab_live_guard(context, settings=settings, action_name="block_ip")
    if guarded is not None:
        return guarded

    valid_target, target_error = _validate_ip_target(context.target_value)
    if not valid_target:
        return _warning_result(
            summary="Live block_ip skipped because target preconditions failed.",
            message=target_error,
            extra=_with_contract_details(
                action_name="block_ip",
                preconditions=preconditions,
                mode_requirements=mode_requirements,
                extra={"target_value": context.target_value},
            ),
        )

    assert context.target_value is not None
    backend = settings.automated_response_block_ip_backend.lower()
    if backend == "ledger":
        try:
            _append_json_line(
                settings.automated_response_ledger_path,
                {
                    "timestamp": datetime.now(UTC).isoformat(),
                    "action": "block_ip",
                    "target_value": context.target_value,
                    "policy_name": context.policy_name,
                    "incident_id": str(_incident_uuid_from_payload(context.payload) or ""),
                    "mode": "live",
                },
            )
        except OSError as exc:
            return _failed_result(
                summary=f"Failed to record block_ip for {context.target_value} in lab ledger.",
                message=str(exc),
                extra=_with_contract_details(
                    action_name="block_ip",
                    preconditions=preconditions,
                    mode_requirements=mode_requirements,
                    extra={"backend": "ledger", "target_ip": context.target_value},
                ),
            )
        _create_incident_audit(
            context,
            action="incident.containment.block_ip.recorded",
            details={
                "target_ip": context.target_value,
                "summary": "Lab firewall ledger updated for block_ip action.",
            },
        )
        return _completed_result(
            context,
            summary=f"IP {context.target_value} recorded in lab firewall ledger.",
            message=(
                "AegisCore recorded a built-in lab block_ip action in the response "
                "ledger without issuing system firewall changes."
            ),
            extra=_with_contract_details(
                action_name="block_ip",
                preconditions=preconditions,
                mode_requirements=mode_requirements,
                extra={"backend": "ledger", "target_ip": context.target_value},
            ),
        )

    if backend == "iptables":
        mode_requirements.append("AUTOMATED_RESPONSE_ALLOW_DESTRUCTIVE=true for iptables backend.")
        blocked = _destructive_guard("block_ip", settings=settings)
        if blocked is not None:
            return blocked
        check_cmd = ["iptables", "-C", "INPUT", "-s", context.target_value, "-j", "DROP"]
        add_cmd = ["iptables", "-I", "INPUT", "-s", context.target_value, "-j", "DROP"]
        check_code, check_stdout, check_stderr = _run_command(check_cmd)
        if check_code == 0:
            return _completed_result(
                context,
                summary=f"IP {context.target_value} already blocked in iptables.",
                message="No changes applied because the rule already exists.",
                extra=_with_contract_details(
                    action_name="block_ip",
                    preconditions=preconditions,
                    mode_requirements=mode_requirements,
                    extra={"backend": "iptables", "rule_present": True},
                ),
            )

        add_code, add_stdout, add_stderr = _run_command(add_cmd)
        if add_code != 0:
            return _failed_result(
                summary=f"Failed to block IP {context.target_value} in iptables.",
                message=add_stderr or add_stdout or "iptables insert command failed.",
                extra={
                    **_with_contract_details(
                        action_name="block_ip",
                        preconditions=preconditions,
                        mode_requirements=mode_requirements,
                    ),
                    "backend": "iptables",
                    "check_stderr": check_stderr,
                    "check_stdout": check_stdout,
                    "add_stderr": add_stderr,
                    "add_stdout": add_stdout,
                },
            )

        verify_code, _, verify_stderr = _run_command(check_cmd)
        if verify_code != 0:
            rollback_cmd = [
                "iptables",
                "-D",
                "INPUT",
                "-s",
                context.target_value,
                "-j",
                "DROP",
            ]
            rollback_code, rollback_stdout, rollback_stderr = _run_command(rollback_cmd)
            return _failed_result(
                summary=f"Failed to verify block rule for {context.target_value}; rollback attempted.",
                message="iptables verification failed after insert.",
                extra={
                    **_with_contract_details(
                        action_name="block_ip",
                        preconditions=preconditions,
                        mode_requirements=mode_requirements,
                    ),
                    "backend": "iptables",
                    "verify_stderr": verify_stderr,
                    "rollback_code": rollback_code,
                    "rollback_stdout": rollback_stdout,
                    "rollback_stderr": rollback_stderr,
                },
            )
        return _completed_result(
            context,
            summary=f"IP {context.target_value} blocked via iptables.",
            message=add_stdout or "iptables rule inserted and verified.",
            extra=_with_contract_details(
                action_name="block_ip",
                preconditions=preconditions,
                mode_requirements=mode_requirements,
                extra={"backend": "iptables", "target_ip": context.target_value},
            ),
        )

    if backend == "script" and settings.response_adapter_block_ip_script:
        return_code, stdout, stderr = _run_script(
            settings.response_adapter_block_ip_script,
            context.payload,
        )
        if return_code != 0:
            return _failed_result(
                summary=f"Legacy script failed for block_ip {context.target_value}.",
                message=stderr or stdout or "Legacy block_ip script failed.",
                extra=_with_contract_details(
                    action_name="block_ip",
                    preconditions=preconditions,
                    mode_requirements=mode_requirements,
                    extra={"backend": "script", "return_code": return_code},
                ),
            )
        return _completed_result(
            context,
            summary=f"Legacy script applied block_ip for {context.target_value}.",
            message=stdout or "Legacy block_ip script completed.",
            extra=_with_contract_details(
                action_name="block_ip",
                preconditions=preconditions,
                mode_requirements=mode_requirements,
                extra={"backend": "script", "return_code": return_code},
            ),
        )

    return _warning_result(
        summary=f"Unsupported block_ip backend '{backend}'.",
        message=(
            "Choose AUTOMATED_RESPONSE_BLOCK_IP_BACKEND as 'ledger', 'iptables', or "
            "'script' with a configured script path."
        ),
        extra=_with_contract_details(
            action_name="block_ip",
            preconditions=preconditions,
            mode_requirements=mode_requirements,
            extra={"backend": backend},
        ),
    )


def _execute_disable_user(context: AdapterContext, *, settings: Settings) -> AdapterExecutionResult:
    preconditions = [
        "Resolved target_value must be a safe Linux username.",
    ]
    mode_requirements = [
        "Policy mode must be live for non-simulated execution.",
        "AUTOMATED_RESPONSE_BUILTIN_ADAPTERS_ENABLED=true.",
        "AUTOMATED_RESPONSE_LAB_ADAPTERS_ENABLED=true.",
    ]
    guarded = _lab_live_guard(context, settings=settings, action_name="disable_user")
    if guarded is not None:
        return guarded

    valid_target, target_error = _validate_username_target(context.target_value)
    if not valid_target:
        return _warning_result(
            summary="Live disable_user skipped because target preconditions failed.",
            message=target_error,
            extra=_with_contract_details(
                action_name="disable_user",
                preconditions=preconditions,
                mode_requirements=mode_requirements,
                extra={"target_value": context.target_value},
            ),
        )

    assert context.target_value is not None
    backend = settings.automated_response_disable_user_backend.lower()
    if backend == "ledger":
        try:
            _append_json_line(
                settings.automated_response_ledger_path,
                {
                    "timestamp": datetime.now(UTC).isoformat(),
                    "action": "disable_user",
                    "target_value": context.target_value,
                    "policy_name": context.policy_name,
                    "incident_id": str(_incident_uuid_from_payload(context.payload) or ""),
                    "mode": "live",
                },
            )
        except OSError as exc:
            return _failed_result(
                summary=f"Failed to record disable_user for {context.target_value} in lab ledger.",
                message=str(exc),
                extra=_with_contract_details(
                    action_name="disable_user",
                    preconditions=preconditions,
                    mode_requirements=mode_requirements,
                    extra={"backend": "ledger", "username": context.target_value},
                ),
            )
        _create_incident_audit(
            context,
            action="incident.containment.disable_user.recorded",
            details={
                "username": context.target_value,
                "summary": "Lab endpoint ledger updated for disable_user action.",
            },
        )
        return _completed_result(
            context,
            summary=f"User {context.target_value} recorded in lab endpoint ledger.",
            message=(
                "AegisCore recorded a built-in lab disable_user action without "
                "executing a destructive system account change."
            ),
            extra=_with_contract_details(
                action_name="disable_user",
                preconditions=preconditions,
                mode_requirements=mode_requirements,
                extra={"backend": "ledger", "username": context.target_value},
            ),
        )

    if backend == "linux_lock":
        mode_requirements.append("AUTOMATED_RESPONSE_ALLOW_DESTRUCTIVE=true for linux_lock backend.")
        blocked = _destructive_guard("disable_user", settings=settings)
        if blocked is not None:
            return blocked
        user_check_code, _, user_check_stderr = _run_command(["id", context.target_value])
        if user_check_code != 0:
            return _warning_result(
                summary=f"User {context.target_value} not found for disable_user.",
                message=user_check_stderr or "The target Linux user was not found.",
                extra=_with_contract_details(
                    action_name="disable_user",
                    preconditions=preconditions,
                    mode_requirements=mode_requirements,
                    extra={"backend": "linux_lock", "username": context.target_value},
                ),
            )
        lock_code, lock_stdout, lock_stderr = _run_command(["passwd", "-l", context.target_value])
        if lock_code != 0:
            return _failed_result(
                summary=f"Failed to lock Linux user {context.target_value}.",
                message=lock_stderr or lock_stdout or "passwd -l command failed.",
                extra=_with_contract_details(
                    action_name="disable_user",
                    preconditions=preconditions,
                    mode_requirements=mode_requirements,
                    extra={"backend": "linux_lock", "username": context.target_value},
                ),
            )
        return _completed_result(
            context,
            summary=f"Linux user {context.target_value} locked.",
            message=lock_stdout or "User account lock completed.",
            extra=_with_contract_details(
                action_name="disable_user",
                preconditions=preconditions,
                mode_requirements=mode_requirements,
                extra={"backend": "linux_lock", "username": context.target_value},
            ),
        )

    if backend == "script" and settings.response_adapter_disable_user_script:
        return_code, stdout, stderr = _run_script(
            settings.response_adapter_disable_user_script,
            context.payload,
        )
        if return_code != 0:
            return _failed_result(
                summary=f"Legacy script failed for disable_user {context.target_value}.",
                message=stderr or stdout or "Legacy disable_user script failed.",
                extra=_with_contract_details(
                    action_name="disable_user",
                    preconditions=preconditions,
                    mode_requirements=mode_requirements,
                    extra={"backend": "script", "return_code": return_code},
                ),
            )
        return _completed_result(
            context,
            summary=f"Legacy script applied disable_user for {context.target_value}.",
            message=stdout or "Legacy disable_user script completed.",
            extra=_with_contract_details(
                action_name="disable_user",
                preconditions=preconditions,
                mode_requirements=mode_requirements,
                extra={"backend": "script", "return_code": return_code},
            ),
        )

    return _warning_result(
        summary=f"Unsupported disable_user backend '{backend}'.",
        message=(
            "Choose AUTOMATED_RESPONSE_DISABLE_USER_BACKEND as 'ledger', 'linux_lock', "
            "or 'script' with a configured script path."
        ),
        extra=_with_contract_details(
            action_name="disable_user",
            preconditions=preconditions,
            mode_requirements=mode_requirements,
            extra={"backend": backend},
        ),
    )


def _execute_notify_admin(context: AdapterContext, *, settings: Settings) -> AdapterExecutionResult:
    preconditions = [
        "Execution payload must include a valid incident.id.",
        "Incident record must exist in the database.",
        "NOTIFICATIONS_ENABLED=true.",
    ]
    mode_requirements = [
        "Policy mode must be live for non-simulated execution.",
        "Notification subsystem must be configured with recipients.",
    ]
    if context.mode == ResponseMode.DRY_RUN:
        return _dry_run_result(context)
    if not settings.notifications_enabled:
        return _warning_result(
            summary="Administrator notification skipped because notifications are disabled.",
            message=(
                "Set NOTIFICATIONS_ENABLED=true to allow built-in notify_admin "
                "live delivery through the notification subsystem."
            ),
            extra=_with_contract_details(
                action_name="notify_admin",
                preconditions=preconditions,
                mode_requirements=mode_requirements,
                extra={"notifications_enabled": False},
            ),
        )

    incident_id = _incident_uuid_from_payload(context.payload)
    if incident_id is None:
        return _failed_result(
            summary="Administrator notification failed due to missing incident context.",
            message="Could not resolve incident ID from response execution payload.",
            extra=_with_contract_details(
                action_name="notify_admin",
                preconditions=preconditions,
                mode_requirements=mode_requirements,
                extra={"incident_id": None},
            ),
        )

    incident = context.session.get(Incident, incident_id)
    if incident is None:
        return _failed_result(
            summary="Administrator notification failed due to missing incident record.",
            message=f"Incident {incident_id} was not found for notify_admin execution.",
            extra=_with_contract_details(
                action_name="notify_admin",
                preconditions=preconditions,
                mode_requirements=mode_requirements,
                extra={"incident_id": str(incident_id)},
            ),
        )

    notification_events = send_admin_notification(
        context.session,
        incident=incident,
        trigger_value=f"notify_admin:{context.policy_name}",
    )
    if not notification_events:
        return _warning_result(
            summary="Administrator notification produced no delivery attempts.",
            message=(
                "Notifications are enabled, but no recipients were configured in "
                "NOTIFICATIONS_ADMIN_RECIPIENTS."
            ),
            extra=_with_contract_details(
                action_name="notify_admin",
                preconditions=preconditions,
                mode_requirements=mode_requirements,
                extra={"attempted": 0},
            ),
        )

    failed = [event for event in notification_events if event.status == "failed"]
    delivered = len(notification_events) - len(failed)
    if failed:
        if delivered > 0:
            return _warning_result(
                summary="Administrator notification partially delivered; some recipients failed.",
                message=failed[0].error_message or "One or more notification deliveries failed.",
                extra=_with_contract_details(
                    action_name="notify_admin",
                    preconditions=preconditions,
                    mode_requirements=mode_requirements,
                    extra={
                        "attempted": len(notification_events),
                        "delivered": delivered,
                        "failed": len(failed),
                    },
                ),
            )
        return _failed_result(
            summary="Administrator notification failed for all recipients.",
            message=failed[0].error_message or "Notification delivery failed.",
            extra=_with_contract_details(
                action_name="notify_admin",
                preconditions=preconditions,
                mode_requirements=mode_requirements,
                extra={"attempted": len(notification_events), "delivered": 0, "failed": len(failed)},
            ),
        )

    return _completed_result(
        context,
        summary="Administrator notification delivered through built-in notification service.",
        message=f"Notification events created for {len(notification_events)} recipients.",
        extra=_with_contract_details(
            action_name="notify_admin",
            preconditions=preconditions,
            mode_requirements=mode_requirements,
            extra={"attempted": len(notification_events), "delivered": len(notification_events)},
        ),
    )


def _execute_quarantine_flag(context: AdapterContext, *, settings: Settings) -> AdapterExecutionResult:
    preconditions = [
        "Resolved target_value must contain a hostname.",
        "Execution payload must include a valid incident.id.",
    ]
    mode_requirements = [
        "Policy mode must be live for non-simulated execution.",
        "AUTOMATED_RESPONSE_BUILTIN_ADAPTERS_ENABLED=true.",
        "AUTOMATED_RESPONSE_LAB_ADAPTERS_ENABLED=true.",
    ]
    guarded = _lab_live_guard(context, settings=settings, action_name="quarantine_host_flag")
    if guarded is not None:
        return guarded

    if not context.target_value:
        return _warning_result(
            summary="Live quarantine_host_flag skipped because hostname was missing.",
            message="AegisCore could not resolve a target hostname for quarantine flagging.",
            extra=_with_contract_details(
                action_name="quarantine_host_flag",
                preconditions=preconditions,
                mode_requirements=mode_requirements,
                extra={"target_value": context.target_value},
            ),
        )

    incident_id = _incident_uuid_from_payload(context.payload)
    if incident_id is None:
        return _failed_result(
            summary="Quarantine host flag failed because incident context was missing.",
            message="A valid incident ID was not present in the response execution payload.",
            extra=_with_contract_details(
                action_name="quarantine_host_flag",
                preconditions=preconditions,
                mode_requirements=mode_requirements,
                extra={"incident_id": None},
            ),
        )

    existing_flag = context.session.scalar(
        select(ContainmentFlag).where(
            ContainmentFlag.incident_id == incident_id,
            ContainmentFlag.hostname == context.target_value,
            ContainmentFlag.active.is_(True),
        )
    )
    if existing_flag is None:
        existing_flag = ContainmentFlag(
            incident_id=incident_id,
            hostname=context.target_value,
            state="active",
            source="quarantine_host_flag",
            note=f"Policy {context.policy_name} requested host quarantine flag.",
            active=True,
        )
        context.session.add(existing_flag)
    else:
        existing_flag.note = f"Policy {context.policy_name} refreshed quarantine host flag."
        existing_flag.state = "active"
        existing_flag.active = True
        existing_flag.released_at = None

    _create_incident_audit(
        context,
        action="incident.containment.quarantine_flagged",
        details={
            "hostname": context.target_value,
            "summary": "Host flagged for quarantine review in containment state.",
        },
    )

    tag_write_error: str | None = None
    if settings.automated_response_enable_host_tag_write:
        try:
            _append_json_line(
                settings.automated_response_host_tag_path,
                {
                    "timestamp": datetime.now(UTC).isoformat(),
                    "hostname": context.target_value,
                    "tag": "quarantined",
                    "incident_id": str(incident_id),
                    "source": "quarantine_host_flag",
                },
            )
        except OSError as exc:
            tag_write_error = str(exc)

    if tag_write_error is not None:
        return _warning_result(
            summary=f"Host {context.target_value} quarantine state saved but host tag write failed.",
            message=tag_write_error,
            extra={
                **_with_contract_details(
                    action_name="quarantine_host_flag",
                    preconditions=preconditions,
                    mode_requirements=mode_requirements,
                ),
                "quarantine_flagged": True,
                "host_tag_written": False,
                "host_tag_path": settings.automated_response_host_tag_path,
            },
        )

    return _completed_result(
        context,
        summary=f"Host {context.target_value} flagged for quarantine review.",
        message=(
            "Containment flag persisted for incident investigation."
            if not settings.automated_response_enable_host_tag_write
            else "Containment flag persisted and safe host tag written."
        ),
        extra=_with_contract_details(
            action_name="quarantine_host_flag",
            preconditions=preconditions,
            mode_requirements=mode_requirements,
            extra={
                "quarantine_flagged": True,
                "containment_state": "active",
                "host_tag_written": settings.automated_response_enable_host_tag_write,
                "host_tag_path": settings.automated_response_host_tag_path
                if settings.automated_response_enable_host_tag_write
                else None,
            },
        ),
    )


def _execute_manual_review(context: AdapterContext, *, settings: Settings) -> AdapterExecutionResult:
    preconditions = [
        "Execution payload must include a valid incident.id.",
    ]
    mode_requirements = [
        "Policy mode must be live for non-simulated execution.",
        "AUTOMATED_RESPONSE_BUILTIN_ADAPTERS_ENABLED=true.",
        "AUTOMATED_RESPONSE_LAB_ADAPTERS_ENABLED=true.",
    ]
    guarded = _lab_live_guard(context, settings=settings, action_name="create_manual_review")
    if guarded is not None:
        return guarded

    incident_id = _incident_uuid_from_payload(context.payload)
    if incident_id is None:
        return _failed_result(
            summary="Manual review workflow failed due to missing incident context.",
            message="A valid incident ID was not present in the execution payload.",
            extra=_with_contract_details(
                action_name="create_manual_review",
                preconditions=preconditions,
                mode_requirements=mode_requirements,
                extra={"incident_id": None},
            ),
        )

    _create_incident_audit(
        context,
        action="incident.manual_review.requested",
        details={
            "incident_id": str(incident_id),
            "policy_name": context.policy_name,
            "summary": "Built-in manual review workflow request recorded.",
        },
    )
    try:
        _append_json_line(
            settings.automated_response_ledger_path,
            {
                "timestamp": datetime.now(UTC).isoformat(),
                "action": "create_manual_review",
                "incident_id": str(incident_id),
                "policy_name": context.policy_name,
                "mode": "live",
            },
        )
    except OSError as exc:
        return _warning_result(
            summary="Manual review audit was recorded, but ledger write failed.",
            message=str(exc),
            extra=_with_contract_details(
                action_name="create_manual_review",
                preconditions=preconditions,
                mode_requirements=mode_requirements,
                extra={
                    "manual_review_recorded": True,
                    "manual_review_ledger_written": False,
                    "incident_id": str(incident_id),
                },
            ),
        )
    return _completed_result(
        context,
        summary="Manual review workflow opened.",
        message=(
            "AegisCore recorded a built-in manual review action and persisted "
            "incident audit evidence."
        ),
        extra=_with_contract_details(
            action_name="create_manual_review",
            preconditions=preconditions,
            mode_requirements=mode_requirements,
            extra={
                "manual_review_recorded": True,
                "manual_review_ledger_written": True,
                "incident_id": str(incident_id),
            },
        ),
    )


ADAPTER_MAP: dict[ResponseActionType, Callable[[AdapterContext, Settings], AdapterExecutionResult]] = {
    ResponseActionType.BLOCK_IP: _execute_block_ip,
    ResponseActionType.DISABLE_USER: _execute_disable_user,
    ResponseActionType.QUARANTINE_HOST_FLAG: _execute_quarantine_flag,
    ResponseActionType.CREATE_MANUAL_REVIEW: _execute_manual_review,
    ResponseActionType.NOTIFY_ADMIN: _execute_notify_admin,
}


def execute_adapter(
    context: AdapterContext,
    *,
    settings: Settings,
) -> AdapterExecutionResult:
    adapter = ADAPTER_MAP[context.action_type]
    return adapter(context, settings=settings)
