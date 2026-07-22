"""Endpoints that answer the seven business questions from the brief."""

from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import (
    BudgetEntry,
    Deliverable,
    DeliverableStatus,
    Project,
    ProjectStatus,
    Resource,
    User,
)
from ..schemas import (
    BudgetLine,
    OverAllocatedResource,
    PortfolioSummary,
    ProjectOut,
)
from ..services import over_allocated_resources, project_metrics, serialize_project

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/summary", response_model=PortfolioSummary)
def summary(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    """Q1 + headline numbers for the dashboard."""
    projects = db.query(Project).all()
    metrics = [project_metrics(db, p) for p in projects]
    deliverables = db.query(Deliverable).all()
    today = date.today()

    return PortfolioSummary(
        total_projects=len(projects),
        active_projects=sum(1 for p in projects if p.status == ProjectStatus.active),
        at_risk_projects=sum(1 for m in metrics if m["risk_level"] == "at_risk"),
        completed_projects=sum(
            1 for p in projects if p.status == ProjectStatus.completed
        ),
        total_deliverables=len(deliverables),
        overdue_deliverables=sum(
            1
            for d in deliverables
            if d.due_date
            and d.due_date < today
            and d.status != DeliverableStatus.completed
        ),
        total_resources=db.query(Resource).filter(Resource.is_active.is_(True)).count(),
        over_allocated_resources=len(over_allocated_resources(db)),
        planned_budget=round(sum(p.planned_budget for p in projects), 2),
        consumed_budget=round(
            sum(e.amount for e in db.query(BudgetEntry).all()), 2
        ),
    )


@router.get("/at-risk", response_model=list[ProjectOut])
def at_risk(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    """Q2: which projects are likely to miss their deadline."""
    rows = [serialize_project(db, p) for p in db.query(Project).all()]
    flagged = [r for r in rows if r["risk_level"] in ("at_risk", "watch")]
    order = {"at_risk": 0, "watch": 1}
    return sorted(flagged, key=lambda r: (order[r["risk_level"]], r["end_date"]))


@router.get("/over-allocated", response_model=list[OverAllocatedResource])
def over_allocated(
    threshold: float = 100.0,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Q5: people committed beyond their capacity."""
    return over_allocated_resources(db, threshold)


@router.get("/budget", response_model=list[BudgetLine])
def budget_overview(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    """Q7: planned versus consumed budget, per project."""
    lines = []
    for p in db.query(Project).order_by(Project.code).all():
        consumed = sum(
            e.amount
            for e in db.query(BudgetEntry).filter(BudgetEntry.project_id == p.id).all()
        )
        lines.append(
            BudgetLine(
                project_id=p.id,
                project_code=p.code,
                project_name=p.name,
                planned_budget=round(p.planned_budget, 2),
                consumed_budget=round(consumed, 2),
                consumed_pct=round((consumed / p.planned_budget * 100), 1)
                if p.planned_budget
                else 0.0,
                variance=round(p.planned_budget - consumed, 2),
            )
        )
    return lines


@router.get("/resource-utilisation")
def resource_utilisation(
    db: Session = Depends(get_db), _: User = Depends(get_current_user)
):
    """Q3: how each person's time is spread across projects."""
    live = (ProjectStatus.active, ProjectStatus.planning, ProjectStatus.on_hold)
    out = []
    for r in db.query(Resource).filter(Resource.is_active.is_(True)).order_by(Resource.full_name).all():
        allocations = [a for a in r.allocations if a.project and a.project.status in live]
        total = round(sum(a.allocation_pct for a in allocations), 1)
        out.append(
            {
                "resource_id": r.id,
                "resource_name": r.full_name,
                "department": r.department,
                "job_title": r.job_title,
                "weekly_capacity_hours": r.weekly_capacity_hours,
                "total_allocation_pct": total,
                "committed_hours": round(r.weekly_capacity_hours * total / 100, 1),
                "status": "over" if total > 100 else ("full" if total == 100 else "available"),
                "assignments": [
                    {
                        "project_id": a.project_id,
                        "project_code": a.project.code,
                        "project_name": a.project.name,
                        "allocation_pct": a.allocation_pct,
                        "role_on_project": a.role_on_project,
                    }
                    for a in allocations
                ],
            }
        )
    return out
