"""Sign-in logic."""

from sqlalchemy.orm import Session

from app.core.exceptions import AuthenticationError, AuthorizationError
from app.core.security import create_access_token, verify_password
from app.dto.auth_dto import TokenResponse
from app.models import User
from app.repositories import UserRepository


class AuthService:
    def __init__(self, db: Session):
        self.users = UserRepository(db)

    def authenticate(self, email: str, password: str) -> TokenResponse:
        """Check the credentials and issue a token, or refuse."""
        user = self.users.get_by_email(email)

        # The same message for a missing user and a wrong password, so the
        # response cannot be used to discover which emails are registered.
        if not user or not verify_password(password, user.hashed_password):
            raise AuthenticationError(
                "That email and password combination does not match an account."
            )

        if not user.is_active:
            raise AuthorizationError(
                "This account is deactivated. Ask an administrator to re-enable it."
            )

        return TokenResponse(access_token=create_access_token(user.email, user.role.value))

    def get_user_from_token_subject(self, email: str) -> User:
        """Resolve the email inside a token back to a live user record.

        Reading the user on every request means a deactivated account stops
        working immediately, rather than when its token happens to expire.
        """
        user = self.users.get_by_email(email)
        if not user or not user.is_active:
            raise AuthenticationError()
        return user
