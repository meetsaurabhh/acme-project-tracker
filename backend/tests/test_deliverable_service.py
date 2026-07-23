"""Unit tests for deliverables and the dependency chain builder."""

from datetime import date, timedelta

import pytest

from app.core.exceptions import NotFoundError, ValidationError
from app.dto.deliverable_dto import DeliverableCreateRequest, DeliverableUpdateRequest
from app.models import Deliverable, DeliverableStatus
from app.services import DeliverableService

TODAY = date.today()


def _add(db, project_id, name, depends_on=None, status=DeliverableStatus.not_started, due=None):
    item = Deliverable(
        project_id=project_id,
        name=name,
        status=status,
        depends_on_id=depends_on,
        due_date=due,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


class TestDependencyChain:
    def test_chain_is_ordered_and_indented(self, db_session, healthy_project):
        first = _add(db_session, healthy_project.id, "Design")
        second = _add(db_session, healthy_project.id, "Build", depends_on=first.id)
        _add(db_session, healthy_project.id, "Test", depends_on=second.id)

        chain = DeliverableService(db_session).get_dependency_chain(healthy_project.id)

        assert [node.name for node in chain] == ["Design", "Build", "Test"]
        assert [node.depth for node in chain] == [0, 1, 2]

    def test_waiting_flag_set_when_predecessor_incomplete(self, db_session, healthy_project):
        first = _add(db_session, healthy_project.id, "Design")
        _add(db_session, healthy_project.id, "Build", depends_on=first.id)

        chain = DeliverableService(db_session).get_dependency_chain(healthy_project.id)
        build = next(node for node in chain if node.name == "Build")

        assert build.blocked_by_incomplete is True

    def test_waiting_flag_clear_when_predecessor_done(self, db_session, healthy_project):
        first = _add(
            db_session, healthy_project.id, "Design", status=DeliverableStatus.completed
        )
        _add(db_session, healthy_project.id, "Build", depends_on=first.id)

        chain = DeliverableService(db_session).get_dependency_chain(healthy_project.id)
        build = next(node for node in chain if node.name == "Build")

        assert build.blocked_by_incomplete is False

    def test_circular_reference_does_not_hang(self, db_session, healthy_project):
        """A cycle in the data must still return every node, not loop forever."""
        first = _add(db_session, healthy_project.id, "A")
        second = _add(db_session, healthy_project.id, "B", depends_on=first.id)
        first.depends_on_id = second.id
        db_session.commit()

        chain = DeliverableService(db_session).get_dependency_chain(healthy_project.id)

        assert len(chain) == 2

    def test_empty_project_returns_empty_chain(self, db_session, healthy_project):
        chain = DeliverableService(db_session).get_dependency_chain(healthy_project.id)

        assert chain == []

    def test_missing_project_raises(self, db_session):
        with pytest.raises(NotFoundError):
            DeliverableService(db_session).get_dependency_chain(9999)


class TestDeliverableRules:
    def test_marking_complete_forces_one_hundred_percent(self, db_session, healthy_project):
        item = _add(db_session, healthy_project.id, "Work")
        service = DeliverableService(db_session)

        result = service.update_deliverable(
            item.id, DeliverableUpdateRequest(status=DeliverableStatus.completed)
        )

        # Status and percentage can never contradict each other.
        assert result.completion_pct == 100.0

    def test_deliverable_cannot_depend_on_itself(self, db_session, healthy_project):
        item = _add(db_session, healthy_project.id, "Work")

        with pytest.raises(ValidationError):
            DeliverableService(db_session).update_deliverable(
                item.id, DeliverableUpdateRequest(depends_on_id=item.id)
            )

    def test_deleting_unhooks_dependents(self, db_session, healthy_project):
        first = _add(db_session, healthy_project.id, "First")
        second = _add(db_session, healthy_project.id, "Second", depends_on=first.id)
        service = DeliverableService(db_session)

        service.delete_deliverable(first.id)

        db_session.refresh(second)
        assert second.depends_on_id is None

    def test_overdue_flag_is_calculated(self, db_session, healthy_project):
        _add(
            db_session,
            healthy_project.id,
            "Late work",
            due=TODAY - timedelta(days=5),
            status=DeliverableStatus.in_progress,
        )

        rows = DeliverableService(db_session).list_deliverables(
            project_id=healthy_project.id
        )

        assert rows[0].is_overdue is True

    def test_completed_work_is_never_overdue(self, db_session, healthy_project):
        _add(
            db_session,
            healthy_project.id,
            "Done late",
            due=TODAY - timedelta(days=5),
            status=DeliverableStatus.completed,
        )

        rows = DeliverableService(db_session).list_deliverables(
            project_id=healthy_project.id
        )

        assert rows[0].is_overdue is False

    def test_creating_against_missing_project_is_rejected(self, db_session):
        payload = DeliverableCreateRequest(project_id=9999, name="Orphan")

        with pytest.raises(NotFoundError):
            DeliverableService(db_session).create_deliverable(payload)
