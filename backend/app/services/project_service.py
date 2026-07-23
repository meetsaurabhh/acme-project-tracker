"""Project rules, including the health calculation that drives the dashboard."""

from datetime import date

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.dto.project_dto import (
    ProjectCreateRequest,
    ProjectFilter,
    ProjectResponse,
    ProjectUpdateRequest,
)
from app.models import DeliverableStatus, Project, ProjectStatus
from app.repositories import (
    AllocationRepository,
    BudgetRepository,
    DeliverableRepository,
    ProjectRepository,
)

# --- Thresholds for the health rules. Named so they can be tuned in one place. ---
SCHEDULE_SLIP_POINTS = 20.0     # time used minus work delivered
BUDGET_ALARM_PCT = 90.0         # spend that counts as nearly exhausted
DELIVERY_SAFE_PCT = 75.0        # progress that justifies that spend
RISK_FLAGS_FOR_AT_RISK = 2      # how many warnings before the verdict escalates


class ProjectService:
    def __init__(self, db: Session):
        self.projects = ProjectRepository(db)
        self.deliverables = DeliverableRepository(db)
        self.allocations = AllocationRepository(db)
        self.budget = BudgetRepository(db)

    # ------------------------------------------------------------------ reads
    def list_projects(self, filters: ProjectFilter) -> list[ProjectResponse]:
        """Database filters are applied first, then the calculated risk filter."""
        rows = self.projects.search(filters.search, filters.status, filters.department)
        responses = [self.build_response(p) for p in rows]

        if filters.risk:
            responses = [r for r in responses if r.risk_level == filters.risk]
        return responses

    def get_project(self, project_id: int) -> ProjectResponse:
        return self.build_response(self._get_or_404(project_id))

    def list_departments(self) -> list[str]:
        return self.projects.list_departments()

    # ----------------------------------------------------------------- writes
    def create_project(self, payload: ProjectCreateRequest) -> ProjectResponse:
        if self.projects.get_by_code(payload.code):
            raise ConflictError("That project code is already in use.")
        self._validate_dates(payload.start_date, payload.end_date)

        project = self.projects.create(**payload.model_dump())
        return self.build_response(project)

    def update_project(
        self, project_id: int, payload: ProjectUpdateRequest
    ) -> ProjectResponse:
        project = self._get_or_404(project_id)
        changes = payload.model_dump(exclude_unset=True)

        # Validate against the merged result, not just the submitted fields,
        # so changing only the end date is still checked against the start.
        self._validate_dates(
            changes.get("start_date", project.start_date),
            changes.get("end_date", project.end_date),
        )

        return self.build_response(self.projects.update(project, **changes))

    def delete_project(self, project_id: int) -> None:
        """Cascade rules on the model remove deliverables, assignments and spend."""
        self.projects.delete(self._get_or_404(project_id))

    # -------------------------------------------------------------- health
    def calculate_metrics(self, project: Project) -> dict:
        """Work out progress, burn and the risk verdict for one project.

        This is the heart of the application. Everything it returns is derived
        at read time, so the numbers can never drift out of date.
        """
        deliverables = self.deliverables.list_by_project(project.id)

        # --- Progress: the mean completion across all deliverables ---
        completion = (
            round(sum(d.completion_pct for d in deliverables) / len(deliverables), 1)
            if deliverables
            else 0.0
        )

        # --- Money: how much of the planned budget has been spent ---
        consumed = self.budget.total_for_project(project.id)
        consumed_pct = self._percentage(consumed, project.planned_budget)

        # --- Time: how much of the schedule has been used up ---
        today = date.today()
        total_days = (project.end_date - project.start_date).days or 1
        elapsed_days = (today - project.start_date).days
        time_elapsed_pct = round(max(0.0, min(elapsed_days / total_days, 1.0)) * 100, 1)

        # --- Health verdict ---
        risk_level, reasons = self._assess_risk(
            project, deliverables, completion, consumed_pct, time_elapsed_pct, today
        )

        return {
            "completion_pct": completion,
            "budget_consumed": round(consumed, 2),
            "budget_consumed_pct": consumed_pct,
            "time_elapsed_pct": time_elapsed_pct,
            "deliverable_count": len(deliverables),
            "resource_count": self.allocations.count_by_project(project.id),
            "risk_level": risk_level,
            "risk_reasons": reasons,
        }

    def build_response(self, project: Project) -> ProjectResponse:
        """Combine the stored columns with the calculated ones."""
        response = ProjectResponse.model_validate(project)
        response.manager_name = project.manager.full_name if project.manager else None

        for field, value in self.calculate_metrics(project).items():
            setattr(response, field, value)
        return response

    # ------------------------------------------------------- internal helpers
    def _assess_risk(
        self,
        project: Project,
        deliverables: list,
        completion: float,
        consumed_pct: float,
        time_elapsed_pct: float,
        today: date,
    ) -> tuple[str, list[str]]:
        """Six independent checks. One firing means watch, two means at risk.

        The reasons are returned alongside the verdict so the dashboard can
        explain itself rather than showing an unexplained red dot.
        """
        # Finished and abandoned projects are not judged.
        if project.status in (ProjectStatus.completed, ProjectStatus.cancelled):
            return "closed", []

        reasons: list[str] = []

        # 1. The deadline has passed and the work is not marked done.
        if project.end_date < today:
            reasons.append("Past its end date and not marked complete")

        # 2. The schedule is being consumed faster than work is being delivered.
        if time_elapsed_pct - completion >= SCHEDULE_SLIP_POINTS:
            reasons.append(
                f"Schedule slip: {time_elapsed_pct}% of time used, {completion}% delivered"
            )

        # 3. The money is nearly gone but the work is not nearly done.
        if consumed_pct >= BUDGET_ALARM_PCT and completion < DELIVERY_SAFE_PCT:
            reasons.append(
                f"Budget burn ahead of delivery: {consumed_pct}% spent, {completion}% delivered"
            )

        # 4. Something is explicitly blocked.
        if any(d.status == DeliverableStatus.blocked for d in deliverables):
            reasons.append("One or more deliverables are blocked")

        # 5. Individual pieces of work have missed their own dates.
        overdue = [
            d
            for d in deliverables
            if d.due_date and d.due_date < today and d.status != DeliverableStatus.completed
        ]
        if overdue:
            reasons.append(f"{len(overdue)} overdue deliverable(s)")

        # 6. The project is paused.
        if project.status == ProjectStatus.on_hold:
            reasons.append("Project is on hold")

        if len(reasons) >= RISK_FLAGS_FOR_AT_RISK:
            return "at_risk", reasons
        if len(reasons) == 1:
            return "watch", reasons
        return "on_track", reasons

    @staticmethod
    def _percentage(part: float, whole: float) -> float:
        """Division that returns zero instead of exploding on a zero budget."""
        return round((part / whole) * 100, 1) if whole else 0.0

    @staticmethod
    def _validate_dates(start_date: date, end_date: date) -> None:
        if end_date < start_date:
            raise ValidationError("End date cannot be before the start date.")

    def _get_or_404(self, project_id: int) -> Project:
        project = self.projects.get(project_id)
        if not project:
            raise NotFoundError("No project with that id.")
        return project
