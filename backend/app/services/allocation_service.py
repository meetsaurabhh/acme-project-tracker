"""Rules for assigning people to projects."""

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.dto.allocation_dto import (
    AllocationCreateRequest,
    AllocationResponse,
    AllocationUpdateRequest,
    OverAllocatedResourceResponse,
)
from app.models import LIVE_PROJECT_STATUSES, Allocation
from app.repositories import (
    AllocationRepository,
    ProjectRepository,
    ResourceRepository,
)

DEFAULT_OVER_ALLOCATION_THRESHOLD = 100.0


class AllocationService:
    def __init__(self, db: Session):
        self.allocations = AllocationRepository(db)
        self.resources = ResourceRepository(db)
        self.projects = ProjectRepository(db)

    def list_allocations(
        self, project_id: int | None = None, resource_id: int | None = None
    ) -> list[AllocationResponse]:
        return [
            self._build_response(a)
            for a in self.allocations.search(project_id, resource_id)
        ]

    def create_allocation(self, payload: AllocationCreateRequest) -> AllocationResponse:
        # Both ends of the assignment must exist.
        if not self.projects.get(payload.project_id):
            raise NotFoundError("No project with that id.")
        if not self.resources.get(payload.resource_id):
            raise NotFoundError("No resource with that id.")

        # A person appears once per project. Changing their share is an edit.
        if self.allocations.find_pairing(payload.project_id, payload.resource_id):
            raise ConflictError(
                "That person is already assigned to this project. "
                "Edit the existing assignment instead."
            )

        return self._build_response(self.allocations.create(**payload.model_dump()))

    def update_allocation(
        self, allocation_id: int, payload: AllocationUpdateRequest
    ) -> AllocationResponse:
        allocation = self._get_or_404(allocation_id)
        changes = payload.model_dump(exclude_unset=True)
        return self._build_response(self.allocations.update(allocation, **changes))

    def delete_allocation(self, allocation_id: int) -> None:
        self.allocations.delete(self._get_or_404(allocation_id))

    def find_over_allocated(
        self, threshold: float = DEFAULT_OVER_ALLOCATION_THRESHOLD
    ) -> list[OverAllocatedResourceResponse]:
        """People promised to more work than their week contains.

        Only live projects count: completed and cancelled work releases its
        people, so including it would report phantom over-allocation.
        """
        results: list[OverAllocatedResourceResponse] = []

        for resource in self.resources.list_active():
            live = [
                a
                for a in resource.allocations
                if a.project and a.project.status in LIVE_PROJECT_STATUSES
            ]
            total = round(sum(a.allocation_pct for a in live), 1)

            if total > threshold:
                results.append(
                    OverAllocatedResourceResponse(
                        resource_id=resource.id,
                        resource_name=resource.full_name,
                        department=resource.department,
                        total_allocation_pct=total,
                        project_count=len(live),
                        projects=[a.project.name for a in live],
                    )
                )

        # Worst offenders first, since that is the order a manager acts in.
        return sorted(results, key=lambda r: r.total_allocation_pct, reverse=True)

    def _build_response(self, allocation: Allocation) -> AllocationResponse:
        response = AllocationResponse.model_validate(allocation)
        response.resource_name = (
            allocation.resource.full_name if allocation.resource else None
        )
        response.project_name = allocation.project.name if allocation.project else None
        response.project_code = allocation.project.code if allocation.project else None
        return response

    def _get_or_404(self, allocation_id: int) -> Allocation:
        allocation = self.allocations.get(allocation_id)
        if not allocation:
            raise NotFoundError("No assignment with that id.")
        return allocation
