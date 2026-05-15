from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.audit_log import AuditLog
from app.models.user import User


# Handles database actions related to audit logs.
class AuditLogsRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_for_entity(self, entity_type: str, entity_id: str) -> list[AuditLog]:
        # Gets audit log records for a selected alert, incident, or response action.
        statement = (
            select(AuditLog)
            .options(selectinload(AuditLog.actor).selectinload(User.role))
            .where(
                AuditLog.entity_type == entity_type,
                AuditLog.entity_id == entity_id,
            )
            .order_by(AuditLog.created_at.desc())
        )
        return list(self.session.scalars(statement))

    def create(self, audit_log: AuditLog) -> AuditLog:
        # Adds a new audit log entry to the current database session.
        self.session.add(audit_log)
        return audit_log