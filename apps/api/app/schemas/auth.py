from typing import Annotated, Literal

from pydantic import Field

from app.schemas.base import APIModel
from app.schemas.common import UserResponse


class LoginRequest(APIModel):
    username: str
    password: str


class TokenResponse(APIModel):
    mfa_required: Literal[False] = False
    access_token: str
    token_type: str
    expires_in: int
    user: UserResponse


class LoginMfaRequiredResponse(APIModel):
    mfa_required: Literal[True] = True
    mfa_token: str


LoginResponse = Annotated[
    TokenResponse | LoginMfaRequiredResponse,
    Field(discriminator="mfa_required"),
]


class MfaSetupResponse(APIModel):
    secret: str
    provisioning_uri: str


class MfaVerifyRequest(APIModel):
    code: str


class MfaValidateRequest(APIModel):
    mfa_token: str
    code: str

