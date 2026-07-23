"""Application entry point: wiring only, no business logic."""

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import settings
from app.core.exceptions import AppError
from app.db.base import Base
from app.db.session import engine

# Importing the models package registers every table on Base.metadata.
import app.models  # noqa: F401

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Centralised project, deliverable, resource and budget tracking.",
)

# --- Allow the React frontend to call this API from its own origin ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Translate service-layer errors into HTTP responses.
#     This is why services can raise plain Python exceptions and stay
#     independent of the web framework. ---
@app.exception_handler(AppError)
def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
    headers = {"WWW-Authenticate": "Bearer"} if exc.status_code == 401 else None
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
        headers=headers,
    )


@app.on_event("startup")
def on_startup() -> None:
    """Create any missing tables.

    Adequate for a workshop. A production system would use Alembic migrations
    so schema changes are versioned and reversible.
    """
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables are ready.")


@app.get("/health", tags=["System"])
def health_check() -> dict:
    """Liveness probe. Used by the deployment scripts and by load balancers."""
    return {"status": "ok", "version": settings.app_version}


# --- Every route in the application, mounted under /api ---
app.include_router(api_router)
