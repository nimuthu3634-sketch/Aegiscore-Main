from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import RoleName
from app.models.role import Role


class RolesRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_name(self, name: RoleName) -> Role | None:
        statement = select(Role).where(Role.name == name)
        return self.session.scalar(statement)

    def create(self, role: Role) -> Role:
        self.session.add(role)
        return role

