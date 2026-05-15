from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.analyst_note import AnalystNote
from app.models.enums import NoteTargetType
from app.models.user import User


# Handles database actions related to analyst notes.
class AnalystNotesRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_for_target(
        self,
        target_type: NoteTargetType,
        target_id: UUID,
    ) -> list[AnalystNote]:
        # Gets all notes linked to a specific alert or incident.
        statement = (
            select(AnalystNote)
            .options(selectinload(AnalystNote.author).selectinload(User.role))
            .where(
                AnalystNote.target_type == target_type,
                AnalystNote.target_id == target_id,
            )
            .order_by(AnalystNote.created_at.desc())
        )
        return list(self.session.scalars(statement))

    def create(self, note: AnalystNote) -> AnalystNote:
        # Adds a new analyst note to the current database session.
        self.session.add(note)
        return note