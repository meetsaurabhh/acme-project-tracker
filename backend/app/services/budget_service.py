"""Rules for recorded spend and budget reporting."""

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.dto.budget_dto import (
    BudgetEntryCreateRequest,
    BudgetEntryResponse,
    BudgetEntryUpdateRequest,
    BudgetLineResponse,
)
from app.models import BudgetEntry
from app.repositories import BudgetRepository, ProjectRepository


class BudgetService:
    def __init__(self, db: Session):
        self.budget = BudgetRepository(db)
        self.projects = ProjectRepository(db)

    def list_entries(
        self, project_id: int | None = None, category: str | None = None
    ) -> list[BudgetEntryResponse]:
        return [self._build_response(e) for e in self.budget.search(project_id, category)]

    def create_entry(self, payload: BudgetEntryCreateRequest) -> BudgetEntryResponse:
        if not self.projects.get(payload.project_id):
            raise NotFoundError("No project with that id.")
        return self._build_response(self.budget.create(**payload.model_dump()))

    def update_entry(
        self, entry_id: int, payload: BudgetEntryUpdateRequest
    ) -> BudgetEntryResponse:
        entry = self._get_or_404(entry_id)
        changes = payload.model_dump(exclude_unset=True)
        return self._build_response(self.budget.update(entry, **changes))

    def delete_entry(self, entry_id: int) -> None:
        self.budget.delete(self._get_or_404(entry_id))

    def get_budget_overview(self) -> list[BudgetLineResponse]:
        """Planned against consumed, one line per project."""
        lines: list[BudgetLineResponse] = []

        for project in sorted(self.projects.list_all(), key=lambda p: p.code):
            consumed = self.budget.total_for_project(project.id)

            lines.append(
                BudgetLineResponse(
                    project_id=project.id,
                    project_code=project.code,
                    project_name=project.name,
                    planned_budget=round(project.planned_budget, 2),
                    consumed_budget=round(consumed, 2),
                    consumed_pct=round(consumed / project.planned_budget * 100, 1)
                    if project.planned_budget
                    else 0.0,
                    # Negative variance means the project has overspent.
                    variance=round(project.planned_budget - consumed, 2),
                )
            )

        return lines

    def _build_response(self, entry: BudgetEntry) -> BudgetEntryResponse:
        response = BudgetEntryResponse.model_validate(entry)
        response.project_name = entry.project.name if entry.project else None
        return response

    def _get_or_404(self, entry_id: int) -> BudgetEntry:
        entry = self.budget.get(entry_id)
        if not entry:
            raise NotFoundError("No budget entry with that id.")
        return entry
