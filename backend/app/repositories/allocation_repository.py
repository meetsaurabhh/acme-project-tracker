"""Database access for project assignments."""

from sqlalchemy.orm import Session

from app.models import Allocation
from app.repositories.base_repository import BaseRepository


class AllocationRepository(BaseRepository[Allocation]):
    def __init__(self, db: Session):
        super().__init__(Allocation, db)

    def search(
        self, project_id: int | None = None, resource_id: int | None = None
    ) -> list[Allocation]:
        query = self.db.query(Allocation)
        if project_id:
            query = query.filter(Allocation.project_id == project_id)
        if resource_id:
            query = query.filter(Allocation.resource_id == resource_id)
        return query.all()

    def find_pairing(self, project_id: int, resource_id: int) -> Allocation | None:
        """Enforces one assignment per person per project."""
        return (
            self.db.query(Allocation)
            .filter(
                Allocation.project_id == project_id,
                Allocation.resource_id == resource_id,
            )
            .first()
        )

    def count_by_project(self, project_id: int) -> int:
        return self.db.query(Allocation).filter(Allocation.project_id == project_id).count()
