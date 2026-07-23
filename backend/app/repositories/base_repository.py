"""Generic CRUD shared by every repository.

The repository layer is the only place in the application that writes
SQLAlchemy queries. Services ask repositories for data; they never build a
query themselves. That keeps database concerns in one layer.
"""

from typing import Generic, TypeVar

from sqlalchemy.orm import Session

from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Create, read, update and delete operations common to all entities."""

    def __init__(self, model: type[ModelType], db: Session):
        self.model = model
        self.db = db

    # --- Read ---
    def get(self, record_id: int) -> ModelType | None:
        """Fetch one record by primary key, or None."""
        return self.db.get(self.model, record_id)

    def list_all(self) -> list[ModelType]:
        """Fetch every record. Filtering variants live in the child classes."""
        return self.db.query(self.model).all()

    def count(self) -> int:
        return self.db.query(self.model).count()

    # --- Write ---
    def create(self, **fields) -> ModelType:
        """Insert a record and return it with its generated id populated."""
        record = self.model(**fields)
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def update(self, record: ModelType, **fields) -> ModelType:
        """Apply only the supplied fields, leaving the rest untouched."""
        for key, value in fields.items():
            setattr(record, key, value)
        self.db.commit()
        self.db.refresh(record)
        return record

    def delete(self, record: ModelType) -> None:
        self.db.delete(record)
        self.db.commit()
