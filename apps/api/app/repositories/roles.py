from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import RoleName
from app.models.role import Role


# Handles database operations related to user roles.
class RolesRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_name(self, name: RoleName) -> Role | None:
        # Finds a role by its name, such as admin or analyst.
        statement = select(Role).where(Role.name == name)
        return self.session.scalar(statement)

    def create(self, role: Role) -> Role:
        # Adds a new role to the current database session.
        self.session.add(role)
        return role