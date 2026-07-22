"""Deliverable rules and the dependency chain builder."""

from datetime import date

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationError
from app.dto.deliverable_dto import (
    DeliverableCreateRequest,
    DeliverableResponse,
    DeliverableUpdateRequest,
    DependencyNodeResponse,
)
from app.models import Deliverable, DeliverableStatus
from app.repositories import DeliverableRepository, ProjectRepository


class DeliverableService:
    def __init__(self, db: Session):
        self.deliverables = DeliverableRepository(db)
        self.projects = ProjectRepository(db)

    # ------------------------------------------------------------------ reads
    def list_deliverables(
        self,
        project_id: int | None = None,
        status: DeliverableStatus | None = None,
        search: str | None = None,
        overdue_only: bool = False,
    ) -> list[DeliverableResponse]:
        rows = self.deliverables.search(project_id, status, search)
        responses = [self._build_response(d) for d in rows]

        # Overdue is calculated rather than stored, so it filters after the query.
        if overdue_only:
            responses = [r for r in responses if r.is_overdue]
        return responses

    # ----------------------------------------------------------------- writes
    def create_deliverable(self, payload: DeliverableCreateRequest) -> DeliverableResponse:
        if not self.projects.get(payload.project_id):
            raise NotFoundError("No project with that id.")

        deliverable = self.deliverables.create(**payload.model_dump())
        return self._build_response(deliverable)

    def update_deliverable(
        self, deliverable_id: int, payload: DeliverableUpdateRequest
    ) -> DeliverableResponse:
        deliverable = self._get_or_404(deliverable_id)
        changes = payload.model_dump(exclude_unset=True)

        # A deliverable cannot wait on itself: that would be an infinite chain.
        if changes.get("depends_on_id") == deliverable_id:
            raise ValidationError("A deliverable cannot depend on itself.")

        # Marking something complete implies one hundred percent, so the two
        # fields can never contradict each other.
        if changes.get("status") == DeliverableStatus.completed:
            changes["completion_pct"] = 100.0

        return self._build_response(self.deliverables.update(deliverable, **changes))

    def delete_deliverable(self, deliverable_id: int) -> None:
        deliverable = self._get_or_404(deliverable_id)

        # Anything waiting on this one becomes unblocked rather than orphaned.
        self.deliverables.clear_dependents(deliverable_id)
        self.deliverables.delete(deliverable)

    # ------------------------------------------------------- dependency chain
    def get_dependency_chain(self, project_id: int) -> list[DependencyNodeResponse]:
        """Flatten the project's deliverables into an ordered, indented list.

        Each item carries a depth so the UI can show what waits on what, and a
        flag for whether its predecessor is still unfinished.
        """
        if not self.projects.get(project_id):
            raise NotFoundError("No project with that id.")

        items = self.deliverables.list_by_project(project_id)
        by_id = {d.id: d for d in items}

        # Group deliverables by what they depend on. A missing or invalid
        # predecessor is treated as no predecessor, so nothing gets lost.
        children: dict[int | None, list[Deliverable]] = {}
        for item in items:
            parent_id = item.depends_on_id if item.depends_on_id in by_id else None
            children.setdefault(parent_id, []).append(item)

        ordered: list[DependencyNodeResponse] = []
        visited: set[int] = set()

        def walk(parent_id: int | None, depth: int) -> None:
            """Depth-first walk: a node, then everything that waits on it."""
            for node in sorted(
                children.get(parent_id, []), key=lambda d: (d.due_date or date.max, d.id)
            ):
                if node.id in visited:
                    continue
                visited.add(node.id)

                predecessor = by_id.get(node.depends_on_id) if node.depends_on_id else None
                ordered.append(
                    DependencyNodeResponse(
                        id=node.id,
                        name=node.name,
                        status=node.status,
                        completion_pct=node.completion_pct,
                        due_date=node.due_date,
                        depends_on_id=node.depends_on_id,
                        depth=depth,
                        blocked_by_incomplete=bool(
                            predecessor
                            and predecessor.status != DeliverableStatus.completed
                        ),
                    )
                )
                walk(node.id, depth + 1)

        walk(None, 0)

        # Safety net: if the data contains a circular reference the walk will
        # not reach those nodes, so append them flat rather than losing them.
        for item in items:
            if item.id not in visited:
                ordered.append(
                    DependencyNodeResponse(
                        id=item.id,
                        name=item.name,
                        status=item.status,
                        completion_pct=item.completion_pct,
                        due_date=item.due_date,
                        depends_on_id=item.depends_on_id,
                        depth=0,
                        blocked_by_incomplete=False,
                    )
                )

        return ordered

    # ------------------------------------------------------- internal helpers
    def _build_response(self, deliverable: Deliverable) -> DeliverableResponse:
        """Attach related names and the calculated overdue flag."""
        response = DeliverableResponse.model_validate(deliverable)
        response.owner_name = deliverable.owner.full_name if deliverable.owner else None
        response.depends_on_name = (
            deliverable.depends_on.name if deliverable.depends_on else None
        )
        response.project_name = deliverable.project.name if deliverable.project else None
        response.is_overdue = bool(
            deliverable.due_date
            and deliverable.due_date < date.today()
            and deliverable.status != DeliverableStatus.completed
        )
        return response

    def _get_or_404(self, deliverable_id: int) -> Deliverable:
        deliverable = self.deliverables.get(deliverable_id)
        if not deliverable:
            raise NotFoundError("No deliverable with that id.")
        return deliverable
