"""Shared enumerations.

They live in their own module so both the ORM models and the DTOs can import
them without importing each other.
"""

import enum


class Role(str, enum.Enum):
    """Access level of a person who can sign in."""

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


# Projects in these states still consume people's time.
LIVE_PROJECT_STATUSES = (
    ProjectStatus.planning,
    ProjectStatus.active,
    ProjectStatus.on_hold,
)
