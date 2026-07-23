"""HTTP routes for projects."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_editor
from app.db.session import get_db
from app.dto.deliverable_dto import DependencyNodeResponse
from app.dto.project_dto import (
    ProjectCreateRequest,
    ProjectFilter,
    ProjectResponse,
    ProjectUpdateRequest,
)
from app.models import ProjectStatus, User
from app.services import DeliverableService, ProjectService

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("", response_model=list[ProjectResponse])
def list_projects(
    search: str | None = Query(default=None, description="Matches name, code or description"),
    status: ProjectStatus | None = None,
    department: str | None = None,
    risk: str | None = Query(default=None, description="on_track | watch | at_risk"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Search and filter the portfolio. Answers 'what is the status of each project'."""
    filters = ProjectFilter(search=search, status=status, department=department, risk=risk)
    return ProjectService(db).list_projects(filters)


@router.get("/departments", response_model=list[str])
def list_departments(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    """Distinct departments, used to populate the filter dropdown."""
    return ProjectService(db).list_departments()


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)
):
    return ProjectService(db).get_project(project_id)


@router.get("/{project_id}/dependency-chain", response_model=list[DependencyNodeResponse])
def get_dependency_chain(
    project_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)
):
    """Answers 'what is the dependency chain between deliverables'."""
    return DeliverableService(db).get_dependency_chain(project_id)


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_editor),
):
    return ProjectService(db).create_project(payload)


@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    payload: ProjectUpdateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_editor),
):
    return ProjectService(db).update_project(project_id, payload)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_editor),
):
    """Deleting a project also removes its deliverables, assignments and spend."""
    ProjectService(db).delete_project(project_id)
