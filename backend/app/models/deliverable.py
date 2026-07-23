"""Deliverable entity: a unit of work inside a project."""

from datetime import datetime

from sqlalchemy import Column, Date, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.enums import DeliverableStatus


class Deliverable(Base):
    __tablename__ = "deliverables"

    id = Column(Integer, primary_key=True)
    project_id = Column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )

    # --- Description ---
    name = Column(String(255), nullable=False)
    description = Column(Text)

    # --- Progress ---
    status = Column(
        Enum(DeliverableStatus, name="deliverable_status_enum"),
        nullable=False,
        default=DeliverableStatus.not_started,
    )
    completion_pct = Column(Float, nullable=False, default=0.0)
    due_date = Column(Date, nullable=True)

    # --- Ownership ---
    owner_id = Column(Integer, ForeignKey("resources.id"), nullable=True)

    # --- Dependency: the single deliverable this one waits on.
    #     A self referencing foreign key is what builds the chain. ---
    depends_on_id = Column(Integer, ForeignKey("deliverables.id"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # --- Relationships ---
    project = relationship("Project", back_populates="deliverables")
    owner = relationship("Resource")
    depends_on = relationship("Deliverable", remote_side=[id])
