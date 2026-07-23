"""HTTP routes for assigning people to projects."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_editor
from app.db.session import get_db
from app.dto.allocation_dto import (
    AllocationCreateRequest,
    AllocationResponse,
    AllocationUpdateRequest,
)
from app.models import User
from app.services import AllocationService

router = APIRouter(prefix="/allocations", tags=["Allocations"])


@router.get("", response_model=list[AllocationResponse])
def list_allocations(
    project_id: int | None = None,
    resource_id: int | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return AllocationService(db).list_allocations(project_id, resource_id)


@router.post("", response_model=AllocationResponse, status_code=status.HTTP_201_CREATED)
def create_allocation(
    payload: AllocationCreateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_editor),
):
    return AllocationService(db).create_allocation(payload)


@router.patch("/{allocation_id}", response_model=AllocationResponse)
def update_allocation(
    allocation_id: int,
    payload: AllocationUpdateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_editor),
):
    return AllocationService(db).update_allocation(allocation_id, payload)


@router.delete("/{allocation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_allocation(
    allocation_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_editor),
):
    AllocationService(db).delete_allocation(allocation_id)
