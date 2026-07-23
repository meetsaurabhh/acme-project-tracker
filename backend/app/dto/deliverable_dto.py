"""Data shapes for deliverables and the dependency chain."""

from datetime import date
from typing import Optional

from pydantic import BaseModel

from app.dto.common_dto import ORM_CONFIG
from app.models.enums import DeliverableStatus


class DeliverableBase(BaseModel):
    project_id: int
    name: str
    description: Optional[str] = None
    status: DeliverableStatus = DeliverableStatus.not_started
    due_date: Optional[date] = None
    completion_pct: float = 0.0
    owner_id: Optional[int] = None
    depends_on_id: Optional[int] = None


class DeliverableCreateRequest(DeliverableBase):
    pass


class DeliverableUpdateRequest(BaseModel):
    """Partial update. project_id is absent on purpose: work does not move projects."""

    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[DeliverableStatus] = None
    due_date: Optional[date] = None
    completion_pct: Optional[float] = None
    owner_id: Optional[int] = None
    depends_on_id: Optional[int] = None


class DeliverableResponse(DeliverableBase):
    """Stored fields plus names resolved from related tables."""

    model_config = ORM_CONFIG

    id: int
    owner_name: Optional[str] = None
    depends_on_name: Optional[str] = None
    project_name: Optional[str] = None
    is_overdue: bool = False


class DependencyNodeResponse(BaseModel):
    """One step in the chain, flattened with a depth so the UI can indent it."""

    id: int
    name: str
    status: DeliverableStatus
    completion_pct: float
    due_date: Optional[date] = None
    depends_on_id: Optional[int] = None
    depth: int = 0
    blocked_by_incomplete: bool = False
