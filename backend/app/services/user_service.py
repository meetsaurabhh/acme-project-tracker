"""Account management rules."""

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.security import hash_password
from app.dto.user_dto import UserCreateRequest, UserResponse, UserUpdateRequest
from app.models import User
from app.repositories import UserRepository


class UserService:
    def __init__(self, db: Session):
        self.users = UserRepository(db)

    def list_users(self, search: str | None = None) -> list[UserResponse]:
        return [UserResponse.model_validate(u) for u in self.users.search(search)]

    def create_user(self, payload: UserCreateRequest) -> UserResponse:
        """Emails are the login identifier, so they must be unique."""
        email = payload.email.lower()
        if self.users.get_by_email(email):
            raise ConflictError("That email is already registered.")

        # The plain password never reaches the database.
        user = self.users.create(
            email=email,
            full_name=payload.full_name,
            role=payload.role,
            is_active=payload.is_active,
            hashed_password=hash_password(payload.password),
        )
        return UserResponse.model_validate(user)

    def update_user(self, user_id: int, payload: UserUpdateRequest) -> UserResponse:
        user = self._get_or_404(user_id)
        changes = payload.model_dump(exclude_unset=True)

        # A new password has to be hashed before it is stored.
        new_password = changes.pop("password", None)
        if new_password:
            changes["hashed_password"] = hash_password(new_password)

        return UserResponse.model_validate(self.users.update(user, **changes))

    def delete_user(self, user_id: int, current_user: User) -> None:
        user = self._get_or_404(user_id)

        # Guard against an admin locking themselves out of the platform.
        if user.id == current_user.id:
            raise ValidationError("You cannot delete your own account.")

        self.users.delete(user)

    def _get_or_404(self, user_id: int) -> User:
        user = self.users.get(user_id)
        if not user:
            raise NotFoundError("No user with that id.")
        return user
