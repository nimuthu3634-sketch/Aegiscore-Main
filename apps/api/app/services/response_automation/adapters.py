from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from typing import Callable

from app.core.config import Settings
from app.models.enums import ResponseActionType, ResponseMode, ResponseStatus
from app.services.response_automation.types import AdapterExecutionResult


@dataclass(frozen=True)
class AdapterContext:
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


def _script_result_or_none(
    script_path: str | None,
    payload: dict,
) -> tuple[int, str, str] | None:
    if not script_path:
        return None
    return _run_script(script_path, payload)


def _dry_run_result(context: AdapterContext) -> AdapterExecutionResult:
    target_value = context.target_value or "no target resolved"
    return AdapterExecutionResult(
        status=ResponseStatus.COMPLETED,
        summary=f"Dry-run: would execute {context.action_type.value} against {target_value}.",
        message=(
            f"Policy {context.policy_name} matched and AegisCore simulated "
            f"{context.action_type.value} in dry-run mode."
        ),
        details={"simulated": True},
    )


def _safe_live_result(
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


def _execute_destructive_action(
    context: AdapterContext,
    *,
    settings: Settings,
    script_path: str | None,
) -> AdapterExecutionResult:
    if context.mode == ResponseMode.DRY_RUN:
        return _dry_run_result(context)

    if not settings.automated_response_allow_destructive:
        return _warning_result(
            summary=f"Live {context.action_type.value} blocked by safety settings.",
            message=(
                "AegisCore prevented destructive live execution because "
                "AUTOMATED_RESPONSE_ALLOW_DESTRUCTIVE is disabled."
            ),
            extra={"blocked_by_safety": True},
        )

    script_result = _script_result_or_none(script_path, context.payload)
    if script_result is None:
        return _warning_result(
            summary=f"Live {context.action_type.value} skipped because no adapter is configured.",
            message=(
                f"No live adapter script is configured for {context.action_type.value}, "
                "so AegisCore logged the action without executing an external change."
            ),
            extra={"adapter_configured": False},
        )

    return_code, stdout, stderr = script_result
    if return_code != 0:
        return _failed_result(
            summary=f"Live {context.action_type.value} failed.",
            message=stderr or stdout or "External adapter exited with a non-zero status.",
            extra={"return_code": return_code, "stdout": stdout, "stderr": stderr},
        )

    return _safe_live_result(
        context,
        summary=f"Live {context.action_type.value} executed successfully.",
        message=stdout or f"External adapter completed {context.action_type.value}.",
        extra={"return_code": return_code, "stdout": stdout},
    )


def _execute_notify_admin(context: AdapterContext, *, settings: Settings) -> AdapterExecutionResult:
    if context.mode == ResponseMode.DRY_RUN:
        return _dry_run_result(context)

    script_result = _script_result_or_none(
        settings.response_adapter_notify_admin_script,
        context.payload,
    )
    if script_result is None:
        return _safe_live_result(
            context,
            summary="Administrator notification recorded.",
            message=(
                "AegisCore recorded a live administrator notification event without "
                "an external adapter script."
            ),
            extra={"notification_recorded": True},
        )

    return_code, stdout, stderr = script_result
    if return_code != 0:
        return _failed_result(
            summary="Administrator notification failed.",
            message=stderr or stdout or "Notification adapter exited with a non-zero status.",
            extra={"return_code": return_code, "stdout": stdout, "stderr": stderr},
        )

    return _safe_live_result(
        context,
        summary="Administrator notification delivered.",
        message=stdout or "Notification adapter completed successfully.",
        extra={"return_code": return_code, "stdout": stdout},
    )


def _execute_quarantine_flag(context: AdapterContext, *, settings: Settings) -> AdapterExecutionResult:
    if context.mode == ResponseMode.DRY_RUN:
        return _dry_run_result(context)

    script_result = _script_result_or_none(
        settings.response_adapter_quarantine_host_flag_script,
        context.payload,
    )
    if script_result is None:
        return _safe_live_result(
            context,
            summary=f"Host {context.target_value or 'target'} flagged for quarantine review.",
            message=(
                "AegisCore recorded an internal quarantine-host flag for analyst follow-up."
            ),
            extra={"quarantine_flagged": True},
        )

    return_code, stdout, stderr = script_result
    if return_code != 0:
        return _failed_result(
            summary="Quarantine host flag failed.",
            message=stderr or stdout or "Quarantine adapter exited with a non-zero status.",
            extra={"return_code": return_code, "stdout": stdout, "stderr": stderr},
        )

    return _safe_live_result(
        context,
        summary="Host quarantine flag applied.",
        message=stdout or "Quarantine flag adapter completed successfully.",
        extra={"return_code": return_code, "stdout": stdout},
    )


def _execute_manual_review(context: AdapterContext, *, settings: Settings) -> AdapterExecutionResult:
    if context.mode == ResponseMode.DRY_RUN:
        return _dry_run_result(context)

    script_result = _script_result_or_none(
        settings.response_adapter_create_manual_review_script,
        context.payload,
    )
    if script_result is None:
        return _safe_live_result(
            context,
            summary="Manual review workflow opened.",
            message=(
                "AegisCore recorded a live manual-review action for analyst handling."
            ),
            extra={"manual_review_recorded": True},
        )

    return_code, stdout, stderr = script_result
    if return_code != 0:
        return _failed_result(
            summary="Manual review action failed.",
            message=stderr or stdout or "Manual review adapter exited with a non-zero status.",
            extra={"return_code": return_code, "stdout": stdout, "stderr": stderr},
        )

    return _safe_live_result(
        context,
        summary="Manual review workflow opened.",
        message=stdout or "Manual review adapter completed successfully.",
        extra={"return_code": return_code, "stdout": stdout},
    )


ADAPTER_MAP: dict[ResponseActionType, Callable[[AdapterContext, Settings], AdapterExecutionResult]] = {
    ResponseActionType.BLOCK_IP: lambda context, settings: _execute_destructive_action(
        context,
        settings=settings,
        script_path=settings.response_adapter_block_ip_script,
    ),
    ResponseActionType.DISABLE_USER: lambda context, settings: _execute_destructive_action(
        context,
        settings=settings,
        script_path=settings.response_adapter_disable_user_script,
    ),
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
