"""Repository layer: every database query in the application lives here.

Services depend on repositories, never on SQLAlchemy directly. Swapping the
database or adding caching would touch only this package.
"""

from app.repositories.allocation_repository import AllocationRepository
from app.repositories.budget_repository import BudgetRepository
from app.repositories.deliverable_repository import DeliverableRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.resource_repository import ResourceRepository
from app.repositories.user_repository import UserRepository

__all__ = [
    "AllocationRepository",
    "BudgetRepository",
    "DeliverableRepository",
    "ProjectRepository",
    "ResourceRepository",
    "UserRepository",
]
