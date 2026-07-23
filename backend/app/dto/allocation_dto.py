"""Data shapes for assigning people to projects."""

from datetime import date
from typing import Optional

from pydantic import BaseModel

from app.dto.common_dto import ORM_CONFIG


class AllocationBase(BaseModel):
    project_id: int
    resource_id: int
    allocation_pct: float = 0.0
    role_on_project: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class AllocationCreateRequest(AllocationBase):
    pass


class AllocationUpdateRequest(BaseModel):
    """The pairing cannot change, only the terms of the assignment."""

    allocation_pct: Optional[float] = None
    role_on_project: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class AllocationResponse(AllocationBase):
    model_config = ORM_CONFIG

    id: int
    resource_name: Optional[str] = None
    project_name: Optional[str] = None
    project_code: Optional[str] = None


class OverAllocatedResourceResponse(BaseModel):
    """A person committed to more than a full week of work."""

    resource_id: int
    resource_name: str
    department: Optional[str] = None
    total_allocation_pct: float
    project_count: int
    projects: list[str]
