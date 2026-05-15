from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import RoleName, enum_values

if TYPE_CHECKING:
    from app.models.user import User


# Stores the user roles available in the system.
class Role(Base):
    __tablename__ = "roles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Role name is used for permission checks such as admin or analyst.
    name: Mapped[RoleName] = mapped_column(
        Enum(RoleName, name="rolename", values_callable=enum_values),
        unique=True,
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # One role can be assigned to many users.
    users: Mapped[list["User"]] = relationship(back_populates="role")