"""Database access for user accounts."""

from sqlalchemy.orm import Session

from app.models import User
from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, db: Session):
        super().__init__(User, db)

    def get_by_email(self, email: str) -> User | None:
        """Used at sign-in and on every authenticated request."""
        return self.db.query(User).filter(User.email == email.lower()).first()

    def search(self, term: str | None = None) -> list[User]:
        """List accounts, optionally matching name or email."""
        query = self.db.query(User)
        if term:
            pattern = f"%{term}%"
            query = query.filter(User.full_name.ilike(pattern) | User.email.ilike(pattern))
        return query.order_by(User.full_name).all()
