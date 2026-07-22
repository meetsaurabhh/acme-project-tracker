"""Data shapes for recorded spend."""

from datetime import date
from typing import Optional

from pydantic import BaseModel

from app.dto.common_dto import ORM_CONFIG


class BudgetEntryBase(BaseModel):
    project_id: int
    category: str = "general"
    amount: float = 0.0
    entry_date: date
    description: Optional[str] = None


class BudgetEntryCreateRequest(BudgetEntryBase):
    pass


class BudgetEntryUpdateRequest(BaseModel):
    category: Optional[str] = None
    amount: Optional[float] = None
    entry_date: Optional[date] = None
    description: Optional[str] = None


class BudgetEntryResponse(BudgetEntryBase):
    model_config = ORM_CONFIG

    id: int
    project_name: Optional[str] = None


class BudgetLineResponse(BaseModel):
    """Planned against consumed for one project."""

    project_id: int
    project_code: str
    project_name: str
    planned_budget: float
    consumed_budget: float
    consumed_pct: float
    variance: float  # negative means overspent
