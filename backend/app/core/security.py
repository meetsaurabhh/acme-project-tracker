"""Cryptographic helpers. Nothing here knows about HTTP or the database."""

from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext

from app.core.config import settings

# pbkdf2_sha256 is pure Python, so there is no native library to compile.
_pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """Turn a plain password into a one-way hash for storage."""
    return _pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check a login attempt against the stored hash."""
    return _pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: str, role: str) -> str:
    """Issue a signed token carrying the user's email and role."""
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_minutes)
    payload = {"sub": subject, "role": role, "exp": expires_at}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    """Verify the signature and expiry, then return the token contents."""
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
