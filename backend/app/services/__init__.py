"""Service layer: every business rule in the application lives here.

Services take DTOs in and return DTOs out. They never see an HTTP request and
never write a SQL query, which is what makes them straightforward to unit test.
"""

from app.services.allocation_service import AllocationService
from app.services.analytics_service import AnalyticsService
from app.services.auth_service import AuthService
from app.services.budget_service import BudgetService
from app.services.deliverable_service import DeliverableService
from app.services.project_service import ProjectService
from app.services.resource_service import ResourceService
from app.services.user_service import UserService

__all__ = [
    "AllocationService",
    "AnalyticsService",
    "AuthService",
    "BudgetService",
    "DeliverableService",
    "ProjectService",
    "ResourceService",
    "UserService",
]
