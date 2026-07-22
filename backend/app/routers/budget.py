"""Actual spend recorded against a project."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, require_editor
from ..models import BudgetEntry, User
from ..schemas import BudgetEntryCreate, BudgetEntryOut, BudgetEntryUpdate

router = APIRouter(prefix="/api/budget-entries", tags=["budget"])


def _out(e: BudgetEntry) -> dict:
    return {
        "id": e.id,
        "project_id": e.project_id,
        "category": e.category,
        "amount": e.amount,
        "entry_date": e.entry_date,
        "description": e.description,
        "project_name": e.project.name if e.project else None,
    }


@router.get("", response_model=list[BudgetEntryOut])
def list_entries(
    project_id: int | None = None,
    category: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(BudgetEntry)
    if project_id:
        q = q.filter(BudgetEntry.project_id == project_id)
    if category:
        q = q.filter(BudgetEntry.category == category)
    return [_out(e) for e in q.order_by(BudgetEntry.entry_date.desc()).all()]


@router.post("", response_model=BudgetEntryOut, status_code=201)
def create_entry(
    payload: BudgetEntryCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_editor),
):
    entry = BudgetEntry(**payload.model_dump())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return _out(entry)


@router.patch("/{entry_id}", response_model=BudgetEntryOut)
def update_entry(
    entry_id: int,
    payload: BudgetEntryUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_editor),
):
    entry = db.get(BudgetEntry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="No budget entry with that id.")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(entry, key, value)
    db.commit()
    db.refresh(entry)
    return _out(entry)


@router.delete("/{entry_id}", status_code=204)
def delete_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_editor),
):
    entry = db.get(BudgetEntry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="No budget entry with that id.")
    db.delete(entry)
    db.commit()
