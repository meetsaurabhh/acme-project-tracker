"""Reusable FastAPI dependencies: who is logged in, and what may they do."""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .database import get_db
from .models import Role, User
from .security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

CREDENTIALS_ERROR = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Sign in again - your session is not valid.",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    try:
        payload = decode_access_token(token)
        email = payload.get("sub")
    except Exception:
        raise CREDENTIALS_ERROR
    if not email:
        raise CREDENTIALS_ERROR
    user = db.query(User).filter(User.email == email).first()
    if not user or not user.is_active:
        raise CREDENTIALS_ERROR
    return user


def require_roles(*allowed: Role):
    """Build a dependency that only lets the listed roles through."""

    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Your role ({user.role.value}) cannot perform this action.",
            )
        return user

    return checker


# Convenience shortcuts used by the routers.
require_admin = require_roles(Role.admin)
require_editor = require_roles(Role.admin, Role.manager)
