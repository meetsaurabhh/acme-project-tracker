"""Who is working on what, and how much of their week it takes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, require_editor
from ..models import Allocation, User
from ..schemas import AllocationCreate, AllocationOut, AllocationUpdate

router = APIRouter(prefix="/api/allocations", tags=["allocations"])


def _out(a: Allocation) -> dict:
    return {
        "id": a.id,
        "project_id": a.project_id,
        "resource_id": a.resource_id,
        "allocation_pct": a.allocation_pct,
        "role_on_project": a.role_on_project,
        "start_date": a.start_date,
        "end_date": a.end_date,
        "resource_name": a.resource.full_name if a.resource else None,
        "project_name": a.project.name if a.project else None,
        "project_code": a.project.code if a.project else None,
    }


@router.get("", response_model=list[AllocationOut])
def list_allocations(
    project_id: int | None = None,
    resource_id: int | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(Allocation)
    if project_id:
        q = q.filter(Allocation.project_id == project_id)
    if resource_id:
        q = q.filter(Allocation.resource_id == resource_id)
    return [_out(a) for a in q.all()]


@router.post("", response_model=AllocationOut, status_code=201)
def create_allocation(
    payload: AllocationCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_editor),
):
    existing = (
        db.query(Allocation)
        .filter(
            Allocation.project_id == payload.project_id,
            Allocation.resource_id == payload.resource_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=409,
            detail="That person is already assigned to this project. Edit the existing assignment instead.",
        )
    allocation = Allocation(**payload.model_dump())
    db.add(allocation)
    db.commit()
    db.refresh(allocation)
    return _out(allocation)


@router.patch("/{allocation_id}", response_model=AllocationOut)
def update_allocation(
    allocation_id: int,
    payload: AllocationUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_editor),
):
    allocation = db.get(Allocation, allocation_id)
    if not allocation:
        raise HTTPException(status_code=404, detail="No assignment with that id.")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(allocation, key, value)
    db.commit()
    db.refresh(allocation)
    return _out(allocation)


@router.delete("/{allocation_id}", status_code=204)
def delete_allocation(
    allocation_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_editor),
):
    allocation = db.get(Allocation, allocation_id)
    if not allocation:
        raise HTTPException(status_code=404, detail="No assignment with that id.")
    db.delete(allocation)
    db.commit()
