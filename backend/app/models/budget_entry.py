"""BudgetEntry entity: one line of money actually spent on a project.

Stored as individual entries rather than a running total, so the platform can
answer where the money went and when, not just how much is left.
"""

from datetime import datetime

from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.base import Base


class BudgetEntry(Base):
    __tablename__ = "budget_entries"

    id = Column(Integer, primary_key=True)
    project_id = Column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )

    # --- The spend ---
    category = Column(String(120), nullable=False, default="general")
    amount = Column(Float, nullable=False, default=0.0)
    entry_date = Column(Date, nullable=False)
    description = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)

    # --- Relationships ---
    project = relationship("Project", back_populates="budget_entries")
