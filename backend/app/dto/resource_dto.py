"""Data shapes for people who do the work."""

from typing import Optional

from pydantic import BaseModel, EmailStr

from app.dto.common_dto import ORM_CONFIG


class ResourceBase(BaseModel):
    """Fields shared by create and read."""

    full_name: str
    email: Optional[EmailStr] = None
    job_title: Optional[str] = None
    department: Optional[str] = None
    location: Optional[str] = None
    weekly_capacity_hours: float = 40.0
    is_active: bool = True


class ResourceCreateRequest(ResourceBase):
    pass


class ResourceUpdateRequest(BaseModel):
    """Partial update: send only the fields that change."""

    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    job_title: Optional[str] = None
    department: Optional[str] = None
    location: Optional[str] = None
    weekly_capacity_hours: Optional[float] = None
    is_active: Optional[bool] = None


class ResourceResponse(ResourceBase):
    model_config = ORM_CONFIG
    id: int


class AssignmentSummary(BaseModel):
    """One project a person is committed to, used inside the utilisation view."""

    project_id: int
    project_code: str
    project_name: str
    allocation_pct: float
    role_on_project: Optional[str] = None


class ResourceUtilisationResponse(BaseModel):
    """A person's total load across every live project."""

    resource_id: int
    resource_name: str
    department: Optional[str] = None
    job_title: Optional[str] = None
    weekly_capacity_hours: float
    total_allocation_pct: float
    committed_hours: float
    status: str  # available | full | over
    assignments: list[AssignmentSummary]
