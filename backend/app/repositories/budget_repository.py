"""Database access for recorded spend."""

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import BudgetEntry
from app.repositories.base_repository import BaseRepository


class BudgetRepository(BaseRepository[BudgetEntry]):
    def __init__(self, db: Session):
        super().__init__(BudgetEntry, db)

    def search(
        self, project_id: int | None = None, category: str | None = None
    ) -> list[BudgetEntry]:
        query = self.db.query(BudgetEntry)
        if project_id:
            query = query.filter(BudgetEntry.project_id == project_id)
        if category:
            query = query.filter(BudgetEntry.category == category)
        return query.order_by(BudgetEntry.entry_date.desc()).all()

    def total_for_project(self, project_id: int) -> float:
        """Sum in the database rather than in Python: one row comes back
        instead of every spend line."""
        total = (
            self.db.query(func.coalesce(func.sum(BudgetEntry.amount), 0.0))
            .filter(BudgetEntry.project_id == project_id)
            .scalar()
        )
        return float(total or 0.0)

    def total_all_projects(self) -> float:
        total = self.db.query(func.coalesce(func.sum(BudgetEntry.amount), 0.0)).scalar()
        return float(total or 0.0)
