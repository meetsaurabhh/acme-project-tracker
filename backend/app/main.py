"""FastAPI application entry point."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import Base, engine
from .routers import (
    allocations,
    analytics,
    auth,
    budget,
    deliverables,
    projects,
    resources,
    users,
)

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="ACME Project Tracker API",
    description="Centralised project, deliverable, resource and budget tracking.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    """Create any missing tables. Good enough for a workshop; a production
    system would use Alembic migrations instead."""
    Base.metadata.create_all(bind=engine)
    logging.info("Database tables are ready.")


@app.get("/health", tags=["system"])
def health():
    return {"status": "ok"}


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(projects.router)
app.include_router(deliverables.router)
app.include_router(resources.router)
app.include_router(allocations.router)
app.include_router(budget.router)
app.include_router(analytics.router)
