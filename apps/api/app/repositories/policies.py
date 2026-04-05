from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import DetectionType, ResponsePolicyTarget
from app.models.response_policy import ResponsePolicy


class PoliciesRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_policies(self) -> list[ResponsePolicy]:
        statement = select(ResponsePolicy).order_by(
            ResponsePolicy.enabled.desc(),
            ResponsePolicy.target.asc(),
            ResponsePolicy.detection_type.asc(),
            ResponsePolicy.min_risk_score.desc(),
            ResponsePolicy.name.asc(),
        )
        return list(self.session.scalars(statement))

    def get_policy(self, policy_id: UUID) -> ResponsePolicy | None:
        return self.session.get(ResponsePolicy, policy_id)

    def find_matching_policies(
        self,
        *,
        target: ResponsePolicyTarget,
        detection_type: DetectionType,
        risk_score: float,
    ) -> list[ResponsePolicy]:
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
        self.session.add(policy)
        return policy
