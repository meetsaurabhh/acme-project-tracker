"""People who can be assigned to projects."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, require_editor
from ..models import Resource, User
from ..schemas import ResourceCreate, ResourceOut, ResourceUpdate

router = APIRouter(prefix="/api/resources", tags=["resources"])


@router.get("", response_model=list[ResourceOut])
def list_resources(
    search: str | None = Query(default=None),
    department: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(Resource)
    if search:
        like = f"%{search}%"
        q = q.filter(Resource.full_name.ilike(like) | Resource.job_title.ilike(like))
    if department:
        q = q.filter(Resource.department == department)
    return q.order_by(Resource.full_name).all()


@router.post("", response_model=ResourceOut, status_code=201)
def create_resource(
    payload: ResourceCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_editor),
):
    resource = Resource(**payload.model_dump())
    db.add(resource)
    db.commit()
    db.refresh(resource)
    return resource


@router.patch("/{resource_id}", response_model=ResourceOut)
def update_resource(
    resource_id: int,
    payload: ResourceUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_editor),
):
    resource = db.get(Resource, resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="No resource with that id.")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(resource, key, value)
    db.commit()
    db.refresh(resource)
    return resource


@router.delete("/{resource_id}", status_code=204)
def delete_resource(
    resource_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_editor),
):
    resource = db.get(Resource, resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="No resource with that id.")
    db.delete(resource)
    db.commit()
