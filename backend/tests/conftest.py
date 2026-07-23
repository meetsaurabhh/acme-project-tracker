"""Shared test fixtures.

Every test runs against a throwaway in-memory SQLite database, so the suite
needs no PostgreSQL server and leaves no state behind.
"""

import os
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Set before importing the application so settings pick it up.
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["JWT_SECRET"] = "test-secret-not-used-in-production"

from app.core.security import hash_password  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import (  # noqa: E402
    Allocation,
    BudgetEntry,
    Deliverable,
    DeliverableStatus,
    Project,
    ProjectStatus,
    Resource,
    Role,
    User,
)

TODAY = date.today()


@pytest.fixture
def db_session():
    """A fresh, empty database for each test."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSession()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session):
    """A test client wired to the throwaway database."""

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


# --------------------------------------------------------------- data helpers
@pytest.fixture
def admin_user(db_session) -> User:
    user = User(
        email="admin@test.com",
        full_name="Test Admin",
        role=Role.admin,
        hashed_password=hash_password("Admin@123"),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def manager_user(db_session) -> User:
    user = User(
        email="manager@test.com",
        full_name="Test Manager",
        role=Role.manager,
        hashed_password=hash_password("Manager@123"),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def viewer_user(db_session) -> User:
    user = User(
        email="viewer@test.com",
        full_name="Test Viewer",
        role=Role.viewer,
        hashed_password=hash_password("Viewer@123"),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def resource(db_session) -> Resource:
    person = Resource(
        full_name="Test Engineer",
        email="engineer@test.com",
        job_title="Engineer",
        department="Engineering",
        weekly_capacity_hours=40.0,
    )
    db_session.add(person)
    db_session.commit()
    db_session.refresh(person)
    return person


@pytest.fixture
def healthy_project(db_session) -> Project:
    """A project running exactly to plan: no risk flags expected."""
    project = Project(
        code="PRJ-OK",
        name="Healthy Project",
        department="Engineering",
        status=ProjectStatus.active,
        priority=2,
        start_date=TODAY - timedelta(days=10),
        end_date=TODAY + timedelta(days=90),
        planned_budget=100_000.0,
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


def auth_headers(client: TestClient, email: str, password: str) -> dict:
    """Sign in and return the Authorization header for that user."""
    response = client.post(
        "/api/auth/login",
        data={"username": email, "password": password},
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}
