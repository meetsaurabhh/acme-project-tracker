"""Data shapes for the dashboard figures."""

from pydantic import BaseModel


class PortfolioSummaryResponse(BaseModel):
    """The headline numbers across every project."""

    total_projects: int
    active_projects: int
    at_risk_projects: int
    completed_projects: int
    total_deliverables: int
    overdue_deliverables: int
    total_resources: int
    over_allocated_resources: int
    planned_budget: float
    consumed_budget: float
