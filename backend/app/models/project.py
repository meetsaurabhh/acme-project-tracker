"""Project entity: the unit of work the whole platform is organised around."""

from datetime import datetime

from sqlalchemy import Column, Date, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.enums import ProjectStatus


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True)

    # --- Identification ---
    code = Column(String(32), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    department = Column(String(120), index=True)

    # --- Status and importance (priority 1 is the highest) ---
    status = Column(
        Enum(ProjectStatus, name="project_status_enum"),
        nullable=False,
        default=ProjectStatus.planning,
    )
    priority = Column(Integer, nullable=False, default=3)

    # --- Schedule and money ---
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    planned_budget = Column(Float, nullable=False, default=0.0)

    # --- Ownership ---
    manager_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # --- Relationships. Deleting a project takes its children with it. ---
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
