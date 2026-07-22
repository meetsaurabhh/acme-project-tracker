"""Database access for people who do the work."""

from sqlalchemy.orm import Session

from app.models import Resource
from app.repositories.base_repository import BaseRepository


class ResourceRepository(BaseRepository[Resource]):
    def __init__(self, db: Session):
        super().__init__(Resource, db)

    def search(self, term: str | None = None, department: str | None = None) -> list[Resource]:
        """List people, optionally narrowed by free text or department."""
        query = self.db.query(Resource)
        if term:
            pattern = f"%{term}%"
            query = query.filter(
                Resource.full_name.ilike(pattern) | Resource.job_title.ilike(pattern)
            )
        if department:
            query = query.filter(Resource.department == department)
        return query.order_by(Resource.full_name).all()

    def list_active(self) -> list[Resource]:
        """Only people currently available for assignment."""
        return (
            self.db.query(Resource)
            .filter(Resource.is_active.is_(True))
            .order_by(Resource.full_name)
            .all()
        )

    def count_active(self) -> int:
        return self.db.query(Resource).filter(Resource.is_active.is_(True)).count()
