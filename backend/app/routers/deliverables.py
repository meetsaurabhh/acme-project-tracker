"""Deliverable CRUD."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, require_editor
from ..models import Deliverable, DeliverableStatus, User
from ..schemas import DeliverableCreate, DeliverableOut, DeliverableUpdate

router = APIRouter(prefix="/api/deliverables", tags=["deliverables"])


def _out(d: Deliverable) -> dict:
    return {
        "id": d.id,
        "project_id": d.project_id,
        "name": d.name,
        "description": d.description,
        "status": d.status,
        "due_date": d.due_date,
        "completion_pct": d.completion_pct,
        "owner_id": d.owner_id,
        "depends_on_id": d.depends_on_id,
        "owner_name": d.owner.full_name if d.owner else None,
        "depends_on_name": d.depends_on.name if d.depends_on else None,
        "project_name": d.project.name if d.project else None,
        "is_overdue": bool(
            d.due_date
            and d.due_date < date.today()
            and d.status != DeliverableStatus.completed
        ),
    }


@router.get("", response_model=list[DeliverableOut])
def list_deliverables(
    project_id: int | None = None,
    status: DeliverableStatus | None = None,
    search: str | None = Query(default=None),
    overdue_only: bool = False,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(Deliverable)
    if project_id:
        q = q.filter(Deliverable.project_id == project_id)
    if status:
        q = q.filter(Deliverable.status == status)
    if search:
        q = q.filter(Deliverable.name.ilike(f"%{search}%"))
    rows = [_out(d) for d in q.order_by(Deliverable.due_date, Deliverable.id).all()]
    if overdue_only:
        rows = [r for r in rows if r["is_overdue"]]
    return rows


@router.post("", response_model=DeliverableOut, status_code=201)
def create_deliverable(
    payload: DeliverableCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_editor),
):
    d = Deliverable(**payload.model_dump())
    db.add(d)
    db.commit()
    db.refresh(d)
    return _out(d)


@router.patch("/{deliverable_id}", response_model=DeliverableOut)
def update_deliverable(
    deliverable_id: int,
    payload: DeliverableUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_editor),
):
    d = db.get(Deliverable, deliverable_id)
    if not d:
        raise HTTPException(status_code=404, detail="No deliverable with that id.")
    data = payload.model_dump(exclude_unset=True)
    if data.get("depends_on_id") == deliverable_id:
        raise HTTPException(status_code=400, detail="A deliverable cannot depend on itself.")
    for key, value in data.items():
        setattr(d, key, value)
    if d.status == DeliverableStatus.completed:
        d.completion_pct = 100.0
    db.commit()
    db.refresh(d)
    return _out(d)


@router.delete("/{deliverable_id}", status_code=204)
def delete_deliverable(
    deliverable_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_editor),
):
    d = db.get(Deliverable, deliverable_id)
    if not d:
        raise HTTPException(status_code=404, detail="No deliverable with that id.")
    db.query(Deliverable).filter(Deliverable.depends_on_id == deliverable_id).update(
        {"depends_on_id": None}
    )
    db.delete(d)
    db.commit()
