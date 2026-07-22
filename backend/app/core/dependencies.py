"""Shared FastAPI dependencies: identifying the caller and checking their role."""

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AuthenticationError, AuthorizationError
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models import Role, User
from app.services.auth_service import AuthService

# Tells the interactive docs where the login endpoint is.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_v1_prefix}/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    """Turn the bearer token on the request into a live user record."""
    try:
        payload = decode_access_token(token)
        email = payload.get("sub")
    except Exception:
        # Covers expired, tampered and malformed tokens alike.
        raise AuthenticationError()

    if not email:
        raise AuthenticationError()

    return AuthService(db).get_user_from_token_subject(email)


def require_roles(*allowed_roles: Role):
    """Build a dependency that only lets the listed roles through.

    Authorisation is enforced here, in the backend. The frontend also hides
    buttons a role cannot use, but that is cosmetic and can be bypassed.
    """

    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise AuthorizationError(
                f"Your role ({current_user.role.value}) cannot perform this action."
            )
        return current_user

    return role_checker


# --- Named shortcuts used across the route modules ---
require_admin = require_roles(Role.admin)
require_editor = require_roles(Role.admin, Role.manager)
