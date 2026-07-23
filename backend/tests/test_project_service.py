"""Unit tests for the risk scoring rules.

These are the most valuable tests in the project: the risk logic is the core
business rule, and it can be exercised without any HTTP layer.
"""

from datetime import date, timedelta

import pytest

from app.models import (
    BudgetEntry,
    Deliverable,
    DeliverableStatus,
    Project,
    ProjectStatus,
)
from app.services import ProjectService

TODAY = date.today()


def _make_project(db, **overrides) -> Project:
    """Create a project that is healthy unless the test overrides something."""
    defaults = dict(
        code=f"PRJ-{id(overrides) % 10000}",
        name="Test Project",
        department="Engineering",
        status=ProjectStatus.active,
        priority=2,
        start_date=TODAY - timedelta(days=10),
        end_date=TODAY + timedelta(days=90),
        planned_budget=100_000.0,
    )
    defaults.update(overrides)
    project = Project(**defaults)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


class TestRiskScoring:
    """Each of the six checks, tested in isolation."""

    def test_project_on_plan_is_on_track(self, db_session, healthy_project):
        metrics = ProjectService(db_session).calculate_metrics(healthy_project)

        assert metrics["risk_level"] == "on_track"
        assert metrics["risk_reasons"] == []

    def test_completed_project_is_closed_not_scored(self, db_session):
        project = _make_project(
            db_session,
            status=ProjectStatus.completed,
            end_date=TODAY - timedelta(days=30),
        )

        metrics = ProjectService(db_session).calculate_metrics(project)

        # A finished project must not be flagged just because its date passed.
        assert metrics["risk_level"] == "closed"
        assert metrics["risk_reasons"] == []

    def test_cancelled_project_is_closed(self, db_session):
        project = _make_project(db_session, status=ProjectStatus.cancelled)

        metrics = ProjectService(db_session).calculate_metrics(project)

        assert metrics["risk_level"] == "closed"

    def test_overdue_project_raises_one_flag(self, db_session):
        project = _make_project(
            db_session,
            start_date=TODAY - timedelta(days=100),
            end_date=TODAY - timedelta(days=5),
        )

        metrics = ProjectService(db_session).calculate_metrics(project)

        # Past its end date, and 100% of time used against 0% delivered,
        # so two rules fire and the verdict escalates.
        assert metrics["risk_level"] == "at_risk"
        assert any("end date" in reason for reason in metrics["risk_reasons"])

    def test_on_hold_project_is_flagged(self, db_session):
        project = _make_project(db_session, status=ProjectStatus.on_hold)

        metrics = ProjectService(db_session).calculate_metrics(project)

        assert any("on hold" in reason for reason in metrics["risk_reasons"])

    def test_blocked_deliverable_is_flagged(self, db_session, healthy_project):
        db_session.add(
            Deliverable(
                project_id=healthy_project.id,
                name="Blocked work",
                status=DeliverableStatus.blocked,
                completion_pct=0.0,
            )
        )
        db_session.commit()

        metrics = ProjectService(db_session).calculate_metrics(healthy_project)

        assert any("blocked" in reason for reason in metrics["risk_reasons"])

    def test_budget_burn_ahead_of_delivery_is_flagged(self, db_session):
        # 95% of the schedule gone, so slip fires too; both rules together
        # should produce at_risk.
        project = _make_project(
            db_session,
            start_date=TODAY - timedelta(days=95),
            end_date=TODAY + timedelta(days=5),
            planned_budget=100_000.0,
        )
        db_session.add(
            BudgetEntry(
                project_id=project.id,
                category="labour",
                amount=95_000.0,
                entry_date=TODAY,
            )
        )
        db_session.add(
            Deliverable(
                project_id=project.id,
                name="Barely started",
                status=DeliverableStatus.in_progress,
                completion_pct=10.0,
            )
        )
        db_session.commit()

        metrics = ProjectService(db_session).calculate_metrics(project)

        assert metrics["risk_level"] == "at_risk"
        assert any("Budget burn" in reason for reason in metrics["risk_reasons"])

    def test_one_flag_is_watch_not_at_risk(self, db_session, healthy_project):
        """The escalation boundary: exactly one warning must not say at_risk."""
        db_session.add(
            Deliverable(
                project_id=healthy_project.id,
                name="Blocked work",
                status=DeliverableStatus.blocked,
                completion_pct=0.0,
            )
        )
        db_session.commit()

        metrics = ProjectService(db_session).calculate_metrics(healthy_project)

        assert len(metrics["risk_reasons"]) == 1
        assert metrics["risk_level"] == "watch"


class TestProgressCalculation:
    def test_completion_is_the_mean_across_deliverables(self, db_session, healthy_project):
        for pct in (100.0, 50.0, 0.0):
            db_session.add(
                Deliverable(
                    project_id=healthy_project.id,
                    name=f"Work at {pct}",
                    completion_pct=pct,
                )
            )
        db_session.commit()

        metrics = ProjectService(db_session).calculate_metrics(healthy_project)

        assert metrics["completion_pct"] == 50.0

    def test_project_with_no_deliverables_reports_zero(self, db_session, healthy_project):
        metrics = ProjectService(db_session).calculate_metrics(healthy_project)

        assert metrics["completion_pct"] == 0.0

    def test_budget_percentage_handles_zero_budget(self, db_session):
        """Division by zero must not crash the dashboard."""
        project = _make_project(db_session, planned_budget=0.0)

        metrics = ProjectService(db_session).calculate_metrics(project)

        assert metrics["budget_consumed_pct"] == 0.0

    def test_time_elapsed_never_exceeds_one_hundred(self, db_session):
        project = _make_project(
            db_session,
            start_date=TODAY - timedelta(days=500),
            end_date=TODAY - timedelta(days=100),
        )

        metrics = ProjectService(db_session).calculate_metrics(project)

        assert metrics["time_elapsed_pct"] == 100.0

    def test_future_project_reports_zero_elapsed(self, db_session):
        project = _make_project(
            db_session,
            start_date=TODAY + timedelta(days=10),
            end_date=TODAY + timedelta(days=100),
        )

        metrics = ProjectService(db_session).calculate_metrics(project)

        assert metrics["time_elapsed_pct"] == 0.0


class TestProjectValidation:
    def test_end_date_before_start_date_is_rejected(self, db_session):
        from app.core.exceptions import ValidationError
        from app.dto.project_dto import ProjectCreateRequest

        payload = ProjectCreateRequest(
            code="PRJ-BAD",
            name="Backwards dates",
            start_date=TODAY,
            end_date=TODAY - timedelta(days=1),
        )

        with pytest.raises(ValidationError):
            ProjectService(db_session).create_project(payload)

    def test_duplicate_code_is_rejected(self, db_session, healthy_project):
        from app.core.exceptions import ConflictError
        from app.dto.project_dto import ProjectCreateRequest

        payload = ProjectCreateRequest(
            code=healthy_project.code,
            name="Duplicate code",
            start_date=TODAY,
            end_date=TODAY + timedelta(days=30),
        )

        with pytest.raises(ConflictError):
            ProjectService(db_session).create_project(payload)
