"""HTTP routes for recorded spend."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_editor
from app.db.session import get_db
from app.dto.budget_dto import (
    BudgetEntryCreateRequest,
    BudgetEntryResponse,
    BudgetEntryUpdateRequest,
)
from app.models import User
from app.services import BudgetService

router = APIRouter(prefix="/budget-entries", tags=["Budget"])


@router.get("", response_model=list[BudgetEntryResponse])
def list_entries(
    project_id: int | None = None,
    category: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return BudgetService(db).list_entries(project_id, category)


@router.post("", response_model=BudgetEntryResponse, status_code=status.HTTP_201_CREATED)
def create_entry(
    payload: BudgetEntryCreateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_editor),
):
    return BudgetService(db).create_entry(payload)


@router.patch("/{entry_id}", response_model=BudgetEntryResponse)
def update_entry(
    entry_id: int,
    payload: BudgetEntryUpdateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_editor),
):
    return BudgetService(db).update_entry(entry_id, payload)


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_editor),
):
    BudgetService(db).delete_entry(entry_id)
