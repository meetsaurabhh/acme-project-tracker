"""Assembles every route module into one router.

main.py includes this single object, so adding a new area of the API means
touching this file rather than the application entry point.
"""

from fastapi import APIRouter

from app.api.v1 import (
    allocation_routes,
    analytics_routes,
    auth_routes,
    budget_routes,
    deliverable_routes,
    project_routes,
    resource_routes,
    user_routes,
)
from app.core.config import settings

api_router = APIRouter(prefix=settings.api_v1_prefix)

# --- Identity and access ---
api_router.include_router(auth_routes.router)
api_router.include_router(user_routes.router)

# --- Core domain ---
api_router.include_router(project_routes.router)
api_router.include_router(deliverable_routes.router)
api_router.include_router(resource_routes.router)
api_router.include_router(allocation_routes.router)
api_router.include_router(budget_routes.router)

# --- Reporting ---
api_router.include_router(analytics_routes.router)
