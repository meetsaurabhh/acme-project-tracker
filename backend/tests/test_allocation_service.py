"""Unit tests for capacity and over-allocation rules."""

from datetime import date, timedelta

import pytest

from app.core.exceptions import ConflictError, NotFoundError
from app.dto.allocation_dto import AllocationCreateRequest
from app.models import Allocation, Project, ProjectStatus, Resource
from app.services import AllocationService, ResourceService

TODAY = date.today()


def _make_project(db, status=ProjectStatus.active, code="PRJ-A") -> Project:
    project = Project(
        code=code,
        name=f"Project {code}",
        status=status,
        start_date=TODAY - timedelta(days=10),
        end_date=TODAY + timedelta(days=90),
        planned_budget=50_000.0,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


class TestOverAllocation:
    def test_person_under_capacity_is_not_flagged(self, db_session, resource):
        project = _make_project(db_session)
        db_session.add(
            Allocation(project_id=project.id, resource_id=resource.id, allocation_pct=80.0)
        )
        db_session.commit()

        flagged = AllocationService(db_session).find_over_allocated()

        assert flagged == []

    def test_person_exactly_at_capacity_is_not_flagged(self, db_session, resource):
        """100% is full, not over. The boundary matters."""
        project = _make_project(db_session)
        db_session.add(
            Allocation(project_id=project.id, resource_id=resource.id, allocation_pct=100.0)
        )
        db_session.commit()

        flagged = AllocationService(db_session).find_over_allocated()

        assert flagged == []

    def test_person_over_capacity_is_flagged(self, db_session, resource):
        first = _make_project(db_session, code="PRJ-A")
        second = _make_project(db_session, code="PRJ-B")
        db_session.add_all(
            [
                Allocation(project_id=first.id, resource_id=resource.id, allocation_pct=70.0),
                Allocation(project_id=second.id, resource_id=resource.id, allocation_pct=60.0),
            ]
        )
        db_session.commit()

        flagged = AllocationService(db_session).find_over_allocated()

        assert len(flagged) == 1
        assert flagged[0].total_allocation_pct == 130.0
        assert flagged[0].project_count == 2

    def test_completed_projects_release_their_people(self, db_session, resource):
        """Finished work must not count against someone's capacity."""
        live = _make_project(db_session, code="PRJ-LIVE")
        done = _make_project(db_session, status=ProjectStatus.completed, code="PRJ-DONE")
        db_session.add_all(
            [
                Allocation(project_id=live.id, resource_id=resource.id, allocation_pct=70.0),
                Allocation(project_id=done.id, resource_id=resource.id, allocation_pct=80.0),
            ]
        )
        db_session.commit()

        flagged = AllocationService(db_session).find_over_allocated()

        # 70 + 80 would be 150, but the completed project does not count.
        assert flagged == []

    def test_custom_threshold_is_respected(self, db_session, resource):
        project = _make_project(db_session)
        db_session.add(
            Allocation(project_id=project.id, resource_id=resource.id, allocation_pct=85.0)
        )
        db_session.commit()

        flagged = AllocationService(db_session).find_over_allocated(threshold=80.0)

        assert len(flagged) == 1


class TestAllocationRules:
    def test_same_person_cannot_be_assigned_twice(self, db_session, resource):
        project = _make_project(db_session)
        service = AllocationService(db_session)
        payload = AllocationCreateRequest(
            project_id=project.id, resource_id=resource.id, allocation_pct=50.0
        )
        service.create_allocation(payload)

        with pytest.raises(ConflictError):
            service.create_allocation(payload)

    def test_assigning_to_missing_project_is_rejected(self, db_session, resource):
        payload = AllocationCreateRequest(
            project_id=9999, resource_id=resource.id, allocation_pct=50.0
        )

        with pytest.raises(NotFoundError):
            AllocationService(db_session).create_allocation(payload)

    def test_assigning_missing_person_is_rejected(self, db_session):
        project = _make_project(db_session)
        payload = AllocationCreateRequest(
            project_id=project.id, resource_id=9999, allocation_pct=50.0
        )

        with pytest.raises(NotFoundError):
            AllocationService(db_session).create_allocation(payload)


class TestUtilisation:
    def test_part_time_capacity_is_respected(self, db_session):
        """Someone on 20 hours at 100% is committed to 20 hours, not 40."""
        part_timer = Resource(full_name="Part Timer", weekly_capacity_hours=20.0)
        db_session.add(part_timer)
        db_session.commit()
        db_session.refresh(part_timer)

        project = _make_project(db_session)
        db_session.add(
            Allocation(project_id=project.id, resource_id=part_timer.id, allocation_pct=100.0)
        )
        db_session.commit()

        rows = ResourceService(db_session).get_utilisation()
        row = next(r for r in rows if r.resource_id == part_timer.id)

        assert row.committed_hours == 20.0
        assert row.status == "full"

    def test_unassigned_person_is_available(self, db_session, resource):
        rows = ResourceService(db_session).get_utilisation()
        row = next(r for r in rows if r.resource_id == resource.id)

        assert row.status == "available"
        assert row.total_allocation_pct == 0.0
        assert row.assignments == []
