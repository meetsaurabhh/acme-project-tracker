"""Pydantic schemas: the shape of data coming in and going out of the API."""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from .models import DeliverableStatus, ProjectStatus, Role


# --------------------------------------------------------------------------
# Auth & users
# --------------------------------------------------------------------------
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: Role = Role.viewer
    is_active: bool = True


class UserCreate(UserBase):
    password: str = Field(min_length=6)


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[Role] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(default=None, min_length=6)


class UserOut(UserBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: Optional[datetime] = None


# --------------------------------------------------------------------------
# Resources (people)
# --------------------------------------------------------------------------
class ResourceBase(BaseModel):
    full_name: str
    email: Optional[EmailStr] = None
    job_title: Optional[str] = None
    department: Optional[str] = None
    location: Optional[str] = None
    weekly_capacity_hours: float = 40.0
    is_active: bool = True


class ResourceCreate(ResourceBase):
    pass


class ResourceUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    job_title: Optional[str] = None
    department: Optional[str] = None
    location: Optional[str] = None
    weekly_capacity_hours: Optional[float] = None
    is_active: Optional[bool] = None


class ResourceOut(ResourceBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


# --------------------------------------------------------------------------
# Projects
# --------------------------------------------------------------------------
class ProjectBase(BaseModel):
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


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
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


class ProjectOut(ProjectBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    manager_name: Optional[str] = None
    completion_pct: float = 0.0
    budget_consumed: float = 0.0
    budget_consumed_pct: float = 0.0
    time_elapsed_pct: float = 0.0
    deliverable_count: int = 0
    resource_count: int = 0
    risk_level: str = "on_track"
    risk_reasons: list[str] = []


# --------------------------------------------------------------------------
# Deliverables
# --------------------------------------------------------------------------
class DeliverableBase(BaseModel):
    project_id: int
    name: str
    description: Optional[str] = None
    status: DeliverableStatus = DeliverableStatus.not_started
    due_date: Optional[date] = None
    completion_pct: float = 0.0
    owner_id: Optional[int] = None
    depends_on_id: Optional[int] = None


class DeliverableCreate(DeliverableBase):
    pass


class DeliverableUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[DeliverableStatus] = None
    due_date: Optional[date] = None
    completion_pct: Optional[float] = None
    owner_id: Optional[int] = None
    depends_on_id: Optional[int] = None


class DeliverableOut(DeliverableBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    owner_name: Optional[str] = None
    depends_on_name: Optional[str] = None
    project_name: Optional[str] = None
    is_overdue: bool = False


# --------------------------------------------------------------------------
# Allocations
# --------------------------------------------------------------------------
class AllocationBase(BaseModel):
    project_id: int
    resource_id: int
    allocation_pct: float = 0.0
    role_on_project: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class AllocationCreate(AllocationBase):
    pass


class AllocationUpdate(BaseModel):
    allocation_pct: Optional[float] = None
    role_on_project: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class AllocationOut(AllocationBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    resource_name: Optional[str] = None
    project_name: Optional[str] = None
    project_code: Optional[str] = None


# --------------------------------------------------------------------------
# Budget
# --------------------------------------------------------------------------
class BudgetEntryBase(BaseModel):
    project_id: int
    category: str = "general"
    amount: float = 0.0
    entry_date: date
    description: Optional[str] = None


class BudgetEntryCreate(BudgetEntryBase):
    pass


class BudgetEntryUpdate(BaseModel):
    category: Optional[str] = None
    amount: Optional[float] = None
    entry_date: Optional[date] = None
    description: Optional[str] = None


class BudgetEntryOut(BudgetEntryBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    project_name: Optional[str] = None


# --------------------------------------------------------------------------
# Analytics
# --------------------------------------------------------------------------
class PortfolioSummary(BaseModel):
    total_projects: int
    active_projects: int
    at_risk_projects: int
    completed_projects: int
    total_deliverables: int
    overdue_deliverables: int
    total_resources: int
    over_allocated_resources: int
    planned_budget: float
    consumed_budget: float


class OverAllocatedResource(BaseModel):
    resource_id: int
    resource_name: str
    department: Optional[str] = None
    total_allocation_pct: float
    project_count: int
    projects: list[str]


class BudgetLine(BaseModel):
    project_id: int
    project_code: str
    project_name: str
    planned_budget: float
    consumed_budget: float
    consumed_pct: float
    variance: float


class DependencyNode(BaseModel):
    id: int
    name: str
    status: DeliverableStatus
    completion_pct: float
    due_date: Optional[date] = None
    depends_on_id: Optional[int] = None
    depth: int = 0
    blocked_by_incomplete: bool = False
