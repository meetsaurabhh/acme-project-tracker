"""Rules for the people who do the work."""

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.dto.resource_dto import (
    AssignmentSummary,
    ResourceCreateRequest,
    ResourceResponse,
    ResourceUpdateRequest,
    ResourceUtilisationResponse,
)
from app.models import LIVE_PROJECT_STATUSES, Resource
from app.repositories import ResourceRepository

# Anything above this is more work than there are hours in the week.
FULL_CAPACITY_PCT = 100.0


class ResourceService:
    def __init__(self, db: Session):
        self.resources = ResourceRepository(db)

    def list_resources(
        self, search: str | None = None, department: str | None = None
    ) -> list[ResourceResponse]:
        return [
            ResourceResponse.model_validate(r)
            for r in self.resources.search(search, department)
        ]

    def create_resource(self, payload: ResourceCreateRequest) -> ResourceResponse:
        resource = self.resources.create(**payload.model_dump())
        return ResourceResponse.model_validate(resource)

    def update_resource(
        self, resource_id: int, payload: ResourceUpdateRequest
    ) -> ResourceResponse:
        resource = self._get_or_404(resource_id)
        changes = payload.model_dump(exclude_unset=True)
        return ResourceResponse.model_validate(self.resources.update(resource, **changes))

    def delete_resource(self, resource_id: int) -> None:
        self.resources.delete(self._get_or_404(resource_id))

    def get_utilisation(self) -> list[ResourceUtilisationResponse]:
        """How each person's week is spread across live projects.

        Completed and cancelled projects release their people, so only live
        ones count towards the total.
        """
        results: list[ResourceUtilisationResponse] = []

        for resource in self.resources.list_active():
            live_allocations = [
                a
                for a in resource.allocations
                if a.project and a.project.status in LIVE_PROJECT_STATUSES
            ]
            total_pct = round(sum(a.allocation_pct for a in live_allocations), 1)

            # Capacity is stored per person, so part-time staff are judged
            # against their own week rather than a notional forty hours.
            committed_hours = round(resource.weekly_capacity_hours * total_pct / 100, 1)

            if total_pct > FULL_CAPACITY_PCT:
                status = "over"
            elif total_pct == FULL_CAPACITY_PCT:
                status = "full"
            else:
                status = "available"

            results.append(
                ResourceUtilisationResponse(
                    resource_id=resource.id,
                    resource_name=resource.full_name,
                    department=resource.department,
                    job_title=resource.job_title,
                    weekly_capacity_hours=resource.weekly_capacity_hours,
                    total_allocation_pct=total_pct,
                    committed_hours=committed_hours,
                    status=status,
                    assignments=[
                        AssignmentSummary(
                            project_id=a.project_id,
                            project_code=a.project.code,
                            project_name=a.project.name,
                            allocation_pct=a.allocation_pct,
                            role_on_project=a.role_on_project,
                        )
                        for a in live_allocations
                    ],
                )
            )

        return results

    def _get_or_404(self, resource_id: int) -> Resource:
        resource = self.resources.get(resource_id)
        if not resource:
            raise NotFoundError("No resource with that id.")
        return resource
