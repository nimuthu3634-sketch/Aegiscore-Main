"""Helper functions for dashboard detection count summaries."""

from __future__ import annotations

from app.models.enums import DetectionType


def complete_alerts_by_detection_counts(
    grouped_rows: list[tuple[DetectionType, int]],
) -> list[tuple[str, int]]:
    """Return all supported detection types with their alert counts."""

    # Start with zero counts so missing detection types still appear on the dashboard.
    counts_by_type = {detection.value: 0 for detection in DetectionType}

    # Replace the zero value with the real count returned from the database.
    for detection_type, count in grouped_rows:
        counts_by_type[str(detection_type.value)] = int(count)

    # Return the result in the same order as the DetectionType enum.
    return [(detection.value, counts_by_type[detection.value]) for detection in DetectionType]