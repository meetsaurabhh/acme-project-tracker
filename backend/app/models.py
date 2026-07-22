"""Database tables, expressed as Python classes (SQLAlchemy ORM models)."""

import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from .database import Base


class Role(str, enum.Enum):
    """Who can do what. admin > manager > viewer."""

    admin = "admin"
    manager = "manager"
    viewer = "viewer"


class ProjectStatus(str, enum.Enum):
    planning = "planning"
    active = "active"
    on_hold = "on_hold"
    completed = "completed"
    cancelled = "cancelled"


class DeliverableStatus(str, enum.Enum):
    not_started = "not_started"
    in_progress = "in_progress"
    blocked = "blocked"
    completed = "completed"


class User(Base):
    """A person who can log in to the platform."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(Role, name="role_enum"), nullable=False, default=Role.viewer)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    managed_projects = relationship("Project", back_populates="manager")


class Resource(Base):
    """A person who does the work. Kept separate from User so you can track
    people who never log in (contractors, vendors, shared services)."""

    __tablename__ = "resources"

    id = Column(Integer, primary_key=True)
    full_name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=True)
    job_title = Column(String(120))
    department = Column(String(120), index=True)
    location = Column(String(120))
    # Hours the person can work per week at 100% allocation.
    weekly_capacity_hours = Column(Float, nullable=False, default=40.0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    allocations = relationship(
        "Allocation", back_populates="resource", cascade="all, delete-orphan"
    )


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True)
    code = Column(String(32), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    department = Column(String(120), index=True)
    status = Column(
        Enum(ProjectStatus, name="project_status_enum"),
        nullable=False,
        default=ProjectStatus.planning,
    )
    priority = Column(Integer, nullable=False, default=3)  # 1 = highest
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    planned_budget = Column(Float, nullable=False, default=0.0)
    manager_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    manager = relationship("User", back_populates="managed_projects")
    deliverables = relationship(
        "Deliverable", back_populates="project", cascade="all, delete-orphan"
    )
    allocations = relationship(
        "Allocation", back_populates="project", cascade="all, delete-orphan"
    )
    budget_entries = relationship(
        "BudgetEntry", back_populates="project", cascade="all, delete-orphan"
    )


class Deliverable(Base):
    """A unit of work inside a project. Can depend on another deliverable,
    which is how the dependency chain is built."""

    __tablename__ = "deliverables"

    id = Column(Integer, primary_key=True)
    project_id = Column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(
        Enum(DeliverableStatus, name="deliverable_status_enum"),
        nullable=False,
        default=DeliverableStatus.not_started,
    )
    due_date = Column(Date, nullable=True)
    completion_pct = Column(Float, nullable=False, default=0.0)
    owner_id = Column(Integer, ForeignKey("resources.id"), nullable=True)
    depends_on_id = Column(Integer, ForeignKey("deliverables.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="deliverables")
    owner = relationship("Resource")
    depends_on = relationship("Deliverable", remote_side=[id])


class Allocation(Base):
    """How much of a person's time is committed to a project."""

    __tablename__ = "allocations"
    __table_args__ = (
        UniqueConstraint("project_id", "resource_id", name="uq_project_resource"),
    )

    id = Column(Integer, primary_key=True)
    project_id = Column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    resource_id = Column(
        Integer, ForeignKey("resources.id", ondelete="CASCADE"), nullable=False
    )
    allocation_pct = Column(Float, nullable=False, default=0.0)
    role_on_project = Column(String(120))
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="allocations")
    resource = relationship("Resource", back_populates="allocations")


class BudgetEntry(Base):
    """One line of money actually spent on a project."""

    __tablename__ = "budget_entries"

    id = Column(Integer, primary_key=True)
    project_id = Column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    category = Column(String(120), nullable=False, default="general")
    amount = Column(Float, nullable=False, default=0.0)
    entry_date = Column(Date, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="budget_entries")
