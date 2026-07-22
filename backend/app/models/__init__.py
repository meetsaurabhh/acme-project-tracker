"""ORM entities.

Every model is imported here so that Base.metadata knows about all tables
before create_all runs. Import models from this package, not from the
individual modules, to keep import order predictable.
"""

from app.models.allocation import Allocation
from app.models.budget_entry import BudgetEntry
from app.models.deliverable import Deliverable
from app.models.enums import (
    LIVE_PROJECT_STATUSES,
    DeliverableStatus,
    ProjectStatus,
    Role,
)
from app.models.project import Project
from app.models.resource import Resource
from app.models.user import User

__all__ = [
    "Allocation",
    "BudgetEntry",
    "Deliverable",
    "DeliverableStatus",
    "LIVE_PROJECT_STATUSES",
    "Project",
    "ProjectStatus",
    "Resource",
    "Role",
    "User",
]
