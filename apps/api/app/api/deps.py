from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db_session
from app.models.enums import RoleName
from app.models.user import User
from app.repositories.users import UsersRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
DbSession = Annotated[Session, Depends(get_db_session)]


def get_current_user(
    db: DbSession,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
        subject = payload.get("sub")
        if subject is None:
            raise credentials_exception
        user_id = UUID(str(subject))
    except (ValueError, jwt.InvalidTokenError) as exc:
        raise credentials_exception from exc

    user = UsersRepository(db).get_by_id(user_id)
    if user is None or not user.is_active:
        raise credentials_exception

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_roles(*allowed_roles: RoleName):
    def _role_dependency(current_user: CurrentUser) -> User:
        if current_user.role.name not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role permissions for this action.",
            )
        return current_user

    return _role_dependency


AdminUser = Annotated[User, Depends(require_roles(RoleName.ADMIN))]
OperatorUser = Annotated[
    User,
    Depends(require_roles(RoleName.ADMIN, RoleName.ANALYST)),
]
