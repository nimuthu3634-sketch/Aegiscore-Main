# Shared response automation types used by adapters and execution logic.

from __future__ import annotations

from dataclasses import dataclass

from app.models.enums import ResponseStatus


# Result object returned after an automation adapter finishes running.
@dataclass(frozen=True)
class AdapterExecutionResult:
    # Final status and details saved back to the response action record.
    status: ResponseStatus
    summary: str
    message: str
    details: dict
