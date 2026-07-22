"""Portfolio-wide figures for the dashboard.

This service composes the others rather than querying directly, so the risk
rules and over-allocation rules are defined in exactly one place.
"""

from datetime import date

from sqlalchemy.orm import Session

from app.dto.analytics_dto import PortfolioSummaryResponse
from app.dto.project_dto import ProjectResponse
from app.models import DeliverableStatus, ProjectStatus
from app.repositories import (
    BudgetRepository,
    DeliverableRepository,
    ProjectRepository,
    ResourceRepository,
)
from app.services.allocation_service import AllocationService
from app.services.project_service import ProjectService


class AnalyticsService:
    def __init__(self, db: Session):
        self.projects = ProjectRepository(db)
        self.deliverables = DeliverableRepository(db)
        self.resources = ResourceRepository(db)
        self.budget = BudgetRepository(db)

        # Reused so the health and capacity rules are never duplicated.
        self.project_service = ProjectService(db)
        self.allocation_service = AllocationService(db)

    def get_portfolio_summary(self) -> PortfolioSummaryResponse:
        """The headline numbers across the whole portfolio."""
        projects = self.projects.list_all()
        deliverables = self.deliverables.list_all()
        today = date.today()

        # Risk has to be calculated per project; it is not a stored column.
        at_risk_count = sum(
            1
            for p in projects
            if self.project_service.calculate_metrics(p)["risk_level"] == "at_risk"
        )

        overdue_count = sum(
            1
            for d in deliverables
            if d.due_date and d.due_date < today and d.status != DeliverableStatus.completed
        )

        return PortfolioSummaryResponse(
            total_projects=len(projects),
            active_projects=self.projects.count_by_status(ProjectStatus.active),
            at_risk_projects=at_risk_count,
            completed_projects=self.projects.count_by_status(ProjectStatus.completed),
            total_deliverables=len(deliverables),
            overdue_deliverables=overdue_count,
            total_resources=self.resources.count_active(),
            over_allocated_resources=len(self.allocation_service.find_over_allocated()),
            planned_budget=round(sum(p.planned_budget for p in projects), 2),
            consumed_budget=round(self.budget.total_all_projects(), 2),
        )

    def get_projects_needing_attention(self) -> list[ProjectResponse]:
        """Everything flagged, worst first, then by how soon it is due."""
        responses = [self.project_service.build_response(p) for p in self.projects.list_all()]
        flagged = [r for r in responses if r.risk_level in ("at_risk", "watch")]

        severity_order = {"at_risk": 0, "watch": 1}
        return sorted(flagged, key=lambda r: (severity_order[r.risk_level], r.end_date))
