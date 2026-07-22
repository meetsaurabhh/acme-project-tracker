"""HTTP routes for the dashboard figures.

Every endpoint here answers one of the questions from the business brief.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.dto.allocation_dto import OverAllocatedResourceResponse
from app.dto.analytics_dto import PortfolioSummaryResponse
from app.dto.budget_dto import BudgetLineResponse
from app.dto.project_dto import ProjectResponse
from app.dto.resource_dto import ResourceUtilisationResponse
from app.models import User
from app.services import (
    AllocationService,
    AnalyticsService,
    BudgetService,
    ResourceService,
)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/summary", response_model=PortfolioSummaryResponse)
def get_summary(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    """Headline portfolio numbers for the dashboard."""
    return AnalyticsService(db).get_portfolio_summary()


@router.get("/at-risk", response_model=list[ProjectResponse])
def get_at_risk_projects(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    """Answers 'which projects are at risk of missing their deadlines'."""
    return AnalyticsService(db).get_projects_needing_attention()


@router.get("/over-allocated", response_model=list[OverAllocatedResourceResponse])
def get_over_allocated(
    threshold: float = 100.0,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Answers 'which team members are over-allocated across multiple projects'."""
    return AllocationService(db).find_over_allocated(threshold)


@router.get("/budget", response_model=list[BudgetLineResponse])
def get_budget_overview(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    """Answers 'how much budget has been consumed versus planned'."""
    return BudgetService(db).get_budget_overview()


@router.get("/resource-utilisation", response_model=list[ResourceUtilisationResponse])
def get_resource_utilisation(
    db: Session = Depends(get_db), _: User = Depends(get_current_user)
):
    """Answers 'how are resources allocated across projects'."""
    return ResourceService(db).get_utilisation()
