# Exposes the scoring functions used by the rest of the backend.
from app.services.scoring.rollup import (
    build_incident_priority_summary,
    refresh_incident_priority,
)


# Lazy import avoids circular imports when other services import scoring.
def score_alert(*args, **kwargs):  # noqa: ANN002, ANN003
    from app.services.scoring.service import score_alert as _score_alert

    return _score_alert(*args, **kwargs)


# Wrapper used when a newly ingested alert must be saved and scored together.
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
