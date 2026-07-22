"""Database access for deliverables."""

from sqlalchemy.orm import Session

from app.models import Deliverable, DeliverableStatus
from app.repositories.base_repository import BaseRepository


class DeliverableRepository(BaseRepository[Deliverable]):
    def __init__(self, db: Session):
        super().__init__(Deliverable, db)

    def search(
        self,
        project_id: int | None = None,
        status: DeliverableStatus | None = None,
        term: str | None = None,
    ) -> list[Deliverable]:
        query = self.db.query(Deliverable)
        if project_id:
            query = query.filter(Deliverable.project_id == project_id)
        if status:
            query = query.filter(Deliverable.status == status)
        if term:
            query = query.filter(Deliverable.name.ilike(f"%{term}%"))
        return query.order_by(Deliverable.due_date, Deliverable.id).all()

    def list_by_project(self, project_id: int) -> list[Deliverable]:
        """Used by the health calculation and the dependency chain builder."""
        return self.db.query(Deliverable).filter(Deliverable.project_id == project_id).all()

    def clear_dependents(self, deliverable_id: int) -> None:
        """Before deleting a deliverable, unhook anything that depends on it,
        otherwise the foreign key would block the delete."""
        self.db.query(Deliverable).filter(
            Deliverable.depends_on_id == deliverable_id
        ).update({"depends_on_id": None})
        self.db.commit()
