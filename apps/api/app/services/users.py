"""Business logic for user management operations."""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.audit_log import AuditLog
from app.models.user import User
from app.repositories.audit_logs import AuditLogsRepository
from app.repositories.roles import RolesRepository
from app.repositories.users import UsersRepository
from app.schemas.users import UserCreateRequest, UserCreateResponse
from app.services.serializers import to_user_response


def create_user(
    db: Session,
    payload: UserCreateRequest,
    *,
    actor: User,
) -> UserCreateResponse:
    """Create a new SOC operator account.

    Only admins may call this (enforced at route level).
    Validates uniqueness and role existence before persisting.
    """

    users_repo = UsersRepository(db)

    # ── duplicate guard ──────────────────────────────────────────────
    existing = users_repo.get_by_username(payload.username)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Username '{payload.username}' is already taken.",
        )

    # ── resolve role ─────────────────────────────────────────────────
    roles_repo = RolesRepository(db)
    role = roles_repo.get_by_name(payload.role)
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role '{payload.role.value}' does not exist. Run the seed first.",
        )

    # ── persist user ─────────────────────────────────────────────────
    user = users_repo.create(
        User(
            role=role,
            username=payload.username,
            password_hash=hash_password(payload.password),
            full_name=payload.full_name,
            is_active=True,
        )
    )

    # ── audit trail ──────────────────────────────────────────────────
    AuditLogsRepository(db).create(
        AuditLog(
            actor=actor,
            action="user.created",
            entity_type="user",
            entity_id=str(user.id),
            details={
                "username": user.username,
                "role": payload.role.value,
                "created_by": actor.username,
            },
        )
    )

    db.commit()

    return UserCreateResponse(
        user=to_user_response(user),
        message=f"User '{user.username}' created successfully.",
    )