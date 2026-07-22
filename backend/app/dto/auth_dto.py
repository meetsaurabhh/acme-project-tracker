"""Data shapes for signing in."""

from pydantic import BaseModel


class LoginRequest(BaseModel):
    """Only used when calling the service directly; the HTTP route uses a form."""

    email: str
    password: str


class TokenResponse(BaseModel):
    """What a successful sign-in returns to the browser."""

    access_token: str
    token_type: str = "bearer"
