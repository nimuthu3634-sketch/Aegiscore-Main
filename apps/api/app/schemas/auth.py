from typing import Annotated, Literal

from pydantic import Field

from app.schemas.base import APIModel
from app.schemas.common import UserResponse


# Request body used when a user logs in.
class LoginRequest(APIModel):
    username: str
    password: str


# Response returned after successful login when MFA is not required.
class TokenResponse(APIModel):
    mfa_required: Literal[False] = False
    access_token: str
    token_type: str
    expires_in: int
    user: UserResponse


# Response returned when the user must complete MFA before getting the access token.
class LoginMfaRequiredResponse(APIModel):
    mfa_required: Literal[True] = True
    mfa_token: str


# Login response can be either a normal token response or an MFA-required response.
LoginResponse = Annotated[
    TokenResponse | LoginMfaRequiredResponse,
    Field(discriminator="mfa_required"),
]


# Response used when generating MFA setup details for the user.
class MfaSetupResponse(APIModel):
    secret: str
    provisioning_uri: str


class MfaVerifyRequest(APIModel):
    # Code from the authenticator app during MFA setup.
    code: str


class MfaValidateRequest(APIModel):
    # MFA token and app code are used to complete the login process.
    mfa_token: str
    code: str