"""Helpers for dashboard detection breakdowns (keeps all supported types visible)."""

from __future__ import annotations

from app.models.enums import DetectionType


def complete_alerts_by_detection_counts(
    grouped_rows: list[tuple[DetectionType, int]],
) -> list[tuple[str, int]]:
    """Return one row per supported detection type, filling missing types with count 0."""
    counts_by_type = {detection.value: 0 for detection in DetectionType}
    for detection_type, count in grouped_rows:
        counts_by_type[str(detection_type.value)] = int(count)
    return [(detection.value, counts_by_type[detection.value]) for detection in DetectionType]
