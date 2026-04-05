from __future__ import annotations

from dataclasses import dataclass

from app.models.enums import ResponseStatus


@dataclass(frozen=True)
class AdapterExecutionResult:
    status: ResponseStatus
    summary: str
    message: str
    details: dict
