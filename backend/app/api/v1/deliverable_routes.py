"""HTTP routes for deliverables."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_editor
from app.db.session import get_db
from app.dto.deliverable_dto import (
    DeliverableCreateRequest,
    DeliverableResponse,
    DeliverableUpdateRequest,
)
from app.models import DeliverableStatus, User
from app.services import DeliverableService

router = APIRouter(prefix="/deliverables", tags=["Deliverables"])


@router.get("", response_model=list[DeliverableResponse])
def list_deliverables(
    project_id: int | None = None,
    status: DeliverableStatus | None = None,
    search: str | None = Query(default=None),
    overdue_only: bool = False,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Answers 'what are the key deliverables and their completion status'."""
    return DeliverableService(db).list_deliverables(project_id, status, search, overdue_only)


@router.post("", response_model=DeliverableResponse, status_code=status.HTTP_201_CREATED)
def create_deliverable(
    payload: DeliverableCreateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_editor),
):
    return DeliverableService(db).create_deliverable(payload)


@router.patch("/{deliverable_id}", response_model=DeliverableResponse)
def update_deliverable(
    deliverable_id: int,
    payload: DeliverableUpdateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_editor),
):
    return DeliverableService(db).update_deliverable(deliverable_id, payload)


@router.delete("/{deliverable_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_deliverable(
    deliverable_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_editor),
):
    DeliverableService(db).delete_deliverable(deliverable_id)
