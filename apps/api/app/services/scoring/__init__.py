from app.services.scoring.rollup import (
    build_incident_priority_summary,
    refresh_incident_priority,
)


def score_alert(*args, **kwargs):  # noqa: ANN002, ANN003
    from app.services.scoring.service import score_alert as _score_alert

    return _score_alert(*args, **kwargs)


def persist_and_score_alert(*args, **kwargs):  # noqa: ANN002, ANN003
    from app.services.scoring.service import (
        persist_and_score_alert as _persist_and_score_alert,
    )

    return _persist_and_score_alert(*args, **kwargs)

__all__ = [
    "build_incident_priority_summary",
    "persist_and_score_alert",
    "refresh_incident_priority",
    "score_alert",
]
