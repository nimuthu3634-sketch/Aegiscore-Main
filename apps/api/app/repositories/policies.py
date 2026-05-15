from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import DetectionType, ResponsePolicyTarget
from app.models.response_policy import ResponsePolicy


# Handles database operations related to response automation policies.
class PoliciesRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_policies(self) -> list[ResponsePolicy]:
        # Returns policies in a useful order for the policies page.
        statement = select(ResponsePolicy).order_by(
            ResponsePolicy.enabled.desc(),
            ResponsePolicy.target.asc(),
            ResponsePolicy.detection_type.asc(),
            ResponsePolicy.min_risk_score.desc(),
            ResponsePolicy.name.asc(),
        )
        return list(self.session.scalars(statement))

    def get_policy(self, policy_id: UUID) -> ResponsePolicy | None:
        # Finds one policy using its ID.
        return self.session.get(ResponsePolicy, policy_id)

    def find_matching_policies(
        self,
        *,
        target: ResponsePolicyTarget,
        detection_type: DetectionType,
        risk_score: float,
    ) -> list[ResponsePolicy]:
        # Finds enabled policies that match the alert/incident type and risk score.
        statement = (
            select(ResponsePolicy)
            .where(
                ResponsePolicy.enabled.is_(True),
                ResponsePolicy.target == target,
                ResponsePolicy.detection_type == detection_type,
                ResponsePolicy.min_risk_score <= int(round(risk_score)),
            )
            .order_by(
                ResponsePolicy.min_risk_score.desc(),
                ResponsePolicy.created_at.asc(),
            )
        )
        return list(self.session.scalars(statement))

    def create(self, policy: ResponsePolicy) -> ResponsePolicy:
        # Adds a new response policy to the database session.
        self.session.add(policy)
        return policy