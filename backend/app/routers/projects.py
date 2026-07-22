"""Project CRUD plus search, filter and the per-project dependency chain."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, require_editor
from ..models import Project, ProjectStatus, User
from ..schemas import DependencyNode, ProjectCreate, ProjectOut, ProjectUpdate
from ..services import dependency_chain, serialize_project

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("", response_model=list[ProjectOut])
def list_projects(
    search: str | None = Query(default=None, description="Matches name, code or description"),
    status: ProjectStatus | None = None,
    department: str | None = None,
    risk: str | None = Query(default=None, description="on_track | watch | at_risk"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(Project)
    if search:
        like = f"%{search}%"
        q = q.filter(
            Project.name.ilike(like)
            | Project.code.ilike(like)
            | Project.description.ilike(like)
        )
    if status:
        q = q.filter(Project.status == status)
    if department:
        q = q.filter(Project.department == department)

    rows = [serialize_project(db, p) for p in q.order_by(Project.priority, Project.name).all()]
    if risk:
        rows = [r for r in rows if r["risk_level"] == risk]
    return rows


@router.get("/departments", response_model=list[str])
def list_departments(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    rows = db.query(Project.department).distinct().all()
    return sorted({r[0] for r in rows if r[0]})


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(
    project_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)
):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="No project with that id.")
    return serialize_project(db, project)


@router.get("/{project_id}/dependency-chain", response_model=list[DependencyNode])
def get_dependency_chain(
    project_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)
):
    if not db.get(Project, project_id):
        raise HTTPException(status_code=404, detail="No project with that id.")
    return dependency_chain(db, project_id)


@router.post("", response_model=ProjectOut, status_code=201)
def create_project(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_editor),
):
    if db.query(Project).filter(Project.code == payload.code).first():
        raise HTTPException(status_code=409, detail="That project code is already in use.")
    if payload.end_date < payload.start_date:
        raise HTTPException(status_code=400, detail="End date cannot be before the start date.")
    project = Project(**payload.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    return serialize_project(db, project)


@router.patch("/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: int,
    payload: ProjectUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_editor),
):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="No project with that id.")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(project, key, value)
    if project.end_date < project.start_date:
        raise HTTPException(status_code=400, detail="End date cannot be before the start date.")
    db.commit()
    db.refresh(project)
    return serialize_project(db, project)


@router.delete("/{project_id}", status_code=204)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_editor),
):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="No project with that id.")
    db.delete(project)
    db.commit()
