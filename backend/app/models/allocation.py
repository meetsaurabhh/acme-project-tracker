"""Allocation entity: how much of a person's week a project consumes."""

from datetime import datetime

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.db.base import Base


class Allocation(Base):
    __tablename__ = "allocations"

    # One assignment per person per project. A second one is an edit, not a new row.
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

    # --- The commitment itself ---
    allocation_pct = Column(Float, nullable=False, default=0.0)
    role_on_project = Column(String(120))
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # --- Relationships ---
    project = relationship("Project", back_populates="allocations")
    resource = relationship("Resource", back_populates="allocations")
