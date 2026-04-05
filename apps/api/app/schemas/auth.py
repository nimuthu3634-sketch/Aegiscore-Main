from app.schemas.base import APIModel
from app.schemas.common import UserResponse


class LoginRequest(APIModel):
    username: str
    password: str


class TokenResponse(APIModel):
    access_token: str
    token_type: str
    expires_in: int
    user: UserResponse

