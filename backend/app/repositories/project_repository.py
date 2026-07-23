"""Database access for projects."""

from sqlalchemy.orm import Session

from app.models import Project, ProjectStatus
from app.repositories.base_repository import BaseRepository


class ProjectRepository(BaseRepository[Project]):
    def __init__(self, db: Session):
        super().__init__(Project, db)

    def get_by_code(self, code: str) -> Project | None:
        """Codes are unique, so this is how duplicates are caught before insert."""
        return self.db.query(Project).filter(Project.code == code).first()

    def search(
        self,
        term: str | None = None,
        status: ProjectStatus | None = None,
        department: str | None = None,
    ) -> list[Project]:
        """Database-level filtering. Risk filtering happens in the service,
        because risk is calculated rather than stored."""
        query = self.db.query(Project)
        if term:
            pattern = f"%{term}%"
            query = query.filter(
                Project.name.ilike(pattern)
                | Project.code.ilike(pattern)
                | Project.description.ilike(pattern)
            )
        if status:
            query = query.filter(Project.status == status)
        if department:
            query = query.filter(Project.department == department)
        return query.order_by(Project.priority, Project.name).all()

    def list_departments(self) -> list[str]:
        """Distinct departments, for populating the filter dropdown."""
        rows = self.db.query(Project.department).distinct().all()
        return sorted({row[0] for row in rows if row[0]})

    def count_by_status(self, status: ProjectStatus) -> int:
        return self.db.query(Project).filter(Project.status == status).count()
