from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.user import User


class UsersRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, user_id: UUID) -> User | None:
        statement = (
            select(User)
            .options(selectinload(User.role))
            .where(User.id == user_id)
        )
        return self.session.scalar(statement)

    def get_by_username(self, username: str) -> User | None:
        statement = (
            select(User)
            .options(selectinload(User.role))
            .where(User.username == username)
        )
        return self.session.scalar(statement)

    def create(self, user: User) -> User:
        self.session.add(user)
        return user

    def touch_last_login(self, user: User) -> None:
        user.last_login_at = datetime.now(UTC)

