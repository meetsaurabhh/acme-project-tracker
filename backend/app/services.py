"""Calculations shared by several routers: progress, budget burn and risk."""

from datetime import date

from sqlalchemy.orm import Session

from .models import (
    Allocation,
    BudgetEntry,
    Deliverable,
    DeliverableStatus,
    Project,
    ProjectStatus,
    Resource,
)


def _pct(part: float, whole: float) -> float:
    return round((part / whole) * 100, 1) if whole else 0.0


def project_metrics(db: Session, project: Project) -> dict:
    """Everything the UI needs to judge one project at a glance."""
    deliverables = (
        db.query(Deliverable).filter(Deliverable.project_id == project.id).all()
    )
    completion = (
        round(sum(d.completion_pct for d in deliverables) / len(deliverables), 1)
        if deliverables
        else 0.0
    )

    consumed = sum(
        e.amount
        for e in db.query(BudgetEntry)
        .filter(BudgetEntry.project_id == project.id)
        .all()
    )
    consumed_pct = _pct(consumed, project.planned_budget)

    today = date.today()
    total_days = (project.end_date - project.start_date).days or 1
    elapsed_days = (today - project.start_date).days
    time_elapsed_pct = round(max(0.0, min(elapsed_days / total_days, 1.0)) * 100, 1)

    resource_count = (
        db.query(Allocation).filter(Allocation.project_id == project.id).count()
    )

    # ---- Risk rules. Plain and explainable on purpose. ----
    reasons: list[str] = []
    if project.status in (ProjectStatus.completed, ProjectStatus.cancelled):
        risk = "closed"
    else:
        if project.end_date < today:
            reasons.append("Past its end date and not marked complete")
        if time_elapsed_pct - completion >= 20:
            reasons.append(
                f"Schedule slip: {time_elapsed_pct}% of time used, {completion}% delivered"
            )
        if consumed_pct >= 90 and completion < 75:
            reasons.append(
                f"Budget burn ahead of delivery: {consumed_pct}% spent, {completion}% delivered"
            )
        if any(d.status == DeliverableStatus.blocked for d in deliverables):
            reasons.append("One or more deliverables are blocked")
        overdue = [
            d
            for d in deliverables
            if d.due_date
            and d.due_date < today
            and d.status != DeliverableStatus.completed
        ]
        if overdue:
            reasons.append(f"{len(overdue)} overdue deliverable(s)")

        if project.status == ProjectStatus.on_hold:
            reasons.append("Project is on hold")

        if len(reasons) >= 2:
            risk = "at_risk"
        elif len(reasons) == 1:
            risk = "watch"
        else:
            risk = "on_track"

    return {
        "completion_pct": completion,
        "budget_consumed": round(consumed, 2),
        "budget_consumed_pct": consumed_pct,
        "time_elapsed_pct": time_elapsed_pct,
        "deliverable_count": len(deliverables),
        "resource_count": resource_count,
        "risk_level": risk,
        "risk_reasons": reasons,
    }


def serialize_project(db: Session, project: Project) -> dict:
    data = {
        "id": project.id,
        "code": project.code,
        "name": project.name,
        "description": project.description,
        "department": project.department,
        "status": project.status,
        "priority": project.priority,
        "start_date": project.start_date,
        "end_date": project.end_date,
        "planned_budget": project.planned_budget,
        "manager_id": project.manager_id,
        "manager_name": project.manager.full_name if project.manager else None,
    }
    data.update(project_metrics(db, project))
    return data


def over_allocated_resources(db: Session, threshold: float = 100.0) -> list[dict]:
    """People whose committed percentage across live projects exceeds capacity."""
    results = []
    live = (ProjectStatus.active, ProjectStatus.planning, ProjectStatus.on_hold)
    for resource in db.query(Resource).filter(Resource.is_active.is_(True)).all():
        allocations = [
            a for a in resource.allocations if a.project and a.project.status in live
        ]
        total = round(sum(a.allocation_pct for a in allocations), 1)
        if total > threshold:
            results.append(
                {
                    "resource_id": resource.id,
                    "resource_name": resource.full_name,
                    "department": resource.department,
                    "total_allocation_pct": total,
                    "project_count": len(allocations),
                    "projects": [a.project.name for a in allocations],
                }
            )
    return sorted(results, key=lambda r: r["total_allocation_pct"], reverse=True)


def dependency_chain(db: Session, project_id: int) -> list[dict]:
    """Flatten a project's deliverables into an ordered, depth-tagged chain."""
    items = db.query(Deliverable).filter(Deliverable.project_id == project_id).all()
    by_id = {d.id: d for d in items}
    children: dict[int | None, list[Deliverable]] = {}
    for d in items:
        parent = d.depends_on_id if d.depends_on_id in by_id else None
        children.setdefault(parent, []).append(d)

    ordered: list[dict] = []
    seen: set[int] = set()

    def walk(parent_id, depth):
        for node in sorted(
            children.get(parent_id, []), key=lambda x: (x.due_date or date.max, x.id)
        ):
            if node.id in seen:
                continue
            seen.add(node.id)
            parent = by_id.get(node.depends_on_id) if node.depends_on_id else None
            ordered.append(
                {
                    "id": node.id,
                    "name": node.name,
                    "status": node.status,
                    "completion_pct": node.completion_pct,
                    "due_date": node.due_date,
                    "depends_on_id": node.depends_on_id,
                    "depth": depth,
                    "blocked_by_incomplete": bool(
                        parent and parent.status != DeliverableStatus.completed
                    ),
                }
            )
            walk(node.id, depth + 1)

    walk(None, 0)
    # Safety net for circular references: append anything not yet visited.
    for d in items:
        if d.id not in seen:
            ordered.append(
                {
                    "id": d.id,
                    "name": d.name,
                    "status": d.status,
                    "completion_pct": d.completion_pct,
                    "due_date": d.due_date,
                    "depends_on_id": d.depends_on_id,
                    "depth": 0,
                    "blocked_by_incomplete": False,
                }
            )
    return ordered
