from app.models.enums import DetectionType
from app.repositories.dashboard_detection_counts import complete_alerts_by_detection_counts


def test_complete_alerts_by_detection_counts_fills_zeros_and_orders_enum() -> None:
    rows = [
        (DetectionType.PORT_SCAN, 4),
        (DetectionType.BRUTE_FORCE, 2),
    ]
    result = complete_alerts_by_detection_counts(rows)

    assert [r[0] for r in result] == [d.value for d in DetectionType]
    assert dict(result) == {
        "brute_force": 2,
        "port_scan": 4,
        "file_integrity_violation": 0,
        "unauthorized_user_creation": 0,
    }
