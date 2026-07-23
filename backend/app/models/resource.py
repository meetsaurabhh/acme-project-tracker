"""Resource entity: a person who does the work.

Kept separate from User so the organisation can track contractors and vendors
who never sign in, and sponsors who sign in but never take an assignment.
"""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base


class Resource(Base):
    __tablename__ = "resources"

    id = Column(Integer, primary_key=True)

    # --- Who they are ---
    full_name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=True)
    job_title = Column(String(120))
    department = Column(String(120), index=True)
    location = Column(String(120))

    # --- Capacity: hours available per week at 100% allocation ---
    weekly_capacity_hours = Column(Float, nullable=False, default=40.0)

    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # --- Relationships ---
    allocations = relationship(
        "Allocation", back_populates="resource", cascade="all, delete-orphan"
    )
