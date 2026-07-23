"""User entity: a person who can sign in to the platform."""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.enums import Role


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)

    # --- Identity ---
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)

    # --- Credentials and access ---
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(Role, name="role_enum"), nullable=False, default=Role.viewer)
    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # --- Relationships ---
    managed_projects = relationship("Project", back_populates="manager")
