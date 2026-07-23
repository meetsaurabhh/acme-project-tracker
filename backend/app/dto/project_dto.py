"""Data shapes for projects, including the calculated health fields."""

from datetime import date
from typing import Optional

from pydantic import BaseModel

from app.dto.common_dto import ORM_CONFIG
from app.models.enums import ProjectStatus


class ProjectBase(BaseModel):
    """The fields a user actually types in."""

    code: str
    name: str
    description: Optional[str] = None
    department: Optional[str] = None
    status: ProjectStatus = ProjectStatus.planning
    priority: int = 3
    start_date: date
    end_date: date
    planned_budget: float = 0.0
    manager_id: Optional[int] = None


class ProjectCreateRequest(ProjectBase):
    pass


class ProjectUpdateRequest(BaseModel):
    """Partial update: unsent fields are left untouched."""

    code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    department: Optional[str] = None
    status: Optional[ProjectStatus] = None
    priority: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    planned_budget: Optional[float] = None
    manager_id: Optional[int] = None


class ProjectResponse(ProjectBase):
    """Stored fields plus everything the service layer works out at read time."""

    model_config = ORM_CONFIG

    id: int
    manager_name: Optional[str] = None

    # --- Derived: progress and burn ---
    completion_pct: float = 0.0
    budget_consumed: float = 0.0
    budget_consumed_pct: float = 0.0
    time_elapsed_pct: float = 0.0

    # --- Derived: size ---
    deliverable_count: int = 0
    resource_count: int = 0

    # --- Derived: health verdict and the reasons behind it ---
    risk_level: str = "on_track"
    risk_reasons: list[str] = []


class ProjectFilter(BaseModel):
    """Search and filter options accepted by the project list endpoint."""

    search: Optional[str] = None
    status: Optional[ProjectStatus] = None
    department: Optional[str] = None
    risk: Optional[str] = None
