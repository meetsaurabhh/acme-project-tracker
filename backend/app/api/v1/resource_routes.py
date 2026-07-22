"""HTTP routes for people who do the work."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_editor
from app.db.session import get_db
from app.dto.resource_dto import (
    ResourceCreateRequest,
    ResourceResponse,
    ResourceUpdateRequest,
    ResourceUtilisationResponse,
)
from app.models import User
from app.services import ResourceService

router = APIRouter(prefix="/resources", tags=["Resources"])


@router.get("", response_model=list[ResourceResponse])
def list_resources(
    search: str | None = Query(default=None),
    department: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return ResourceService(db).list_resources(search, department)


@router.get("/utilisation", response_model=list[ResourceUtilisationResponse])
def get_utilisation(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    """Answers 'how are resources allocated across projects'."""
    return ResourceService(db).get_utilisation()


@router.post("", response_model=ResourceResponse, status_code=status.HTTP_201_CREATED)
def create_resource(
    payload: ResourceCreateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_editor),
):
    return ResourceService(db).create_resource(payload)


@router.patch("/{resource_id}", response_model=ResourceResponse)
def update_resource(
    resource_id: int,
    payload: ResourceUpdateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_editor),
):
    return ResourceService(db).update_resource(resource_id, payload)


@router.delete("/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_resource(
    resource_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_editor),
):
    ResourceService(db).delete_resource(resource_id)
