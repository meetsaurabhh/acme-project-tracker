"""Load a realistic demo portfolio into an empty database.

Run from the backend folder:   python -m app.seeds.seed_data
Safe to run twice: it clears the tables first.
"""

import random
from datetime import date, timedelta

from app.core.security import hash_password
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models import (
    Allocation,
    BudgetEntry,
    Deliverable,
    DeliverableStatus,
    Project,
    ProjectStatus,
    Resource,
    Role,
    User,
)

TODAY = date.today()

# --- Accounts, one per role, so access control can be demonstrated ---
DEMO_USERS = [
    ("admin@acme.com", "Ada Okonkwo", Role.admin, "Admin@123"),
    ("manager@acme.com", "Ravi Deshpande", Role.manager, "Manager@123"),
    ("viewer@acme.com", "Sofia Marin", Role.viewer, "Viewer@123"),
]

# --- People available for assignment ---
DEMO_PEOPLE = [
    ("Priya Nair", "Lead Engineer", "Engineering", "Mumbai", 40),
    ("Tom Halvorsen", "Backend Engineer", "Engineering", "Oslo", 40),
    ("Chen Wei", "Data Engineer", "Data", "Singapore", 40),
    ("Marta Ruiz", "UX Designer", "Design", "Madrid", 32),
    ("Danielle Fox", "QA Analyst", "Quality", "Toronto", 40),
    ("Omar Haddad", "DevOps Engineer", "Platform", "Dubai", 40),
    ("Ellie Zhang", "Business Analyst", "Operations", "Mumbai", 40),
    ("Jonas Berg", "Frontend Engineer", "Engineering", "Berlin", 40),
    ("Aisha Bello", "Security Engineer", "Platform", "Lagos", 40),
    ("Luca Rossi", "Product Owner", "Operations", "Milan", 40),
]

# --- Projects. Dates are offsets in days from today, so the demo data stays
#     current no matter when it is loaded. ---
DEMO_PROJECTS = [
    # code, name, department, status, priority, start_offset, end_offset, budget
    ("PRJ-001", "Customer Portal Rebuild", "Engineering", ProjectStatus.active, 1, -120, 30, 480_000),
    ("PRJ-002", "Data Lake Migration", "Data", ProjectStatus.active, 1, -200, -10, 950_000),
    ("PRJ-003", "Mobile Onboarding App", "Engineering", ProjectStatus.active, 2, -60, 120, 320_000),
    ("PRJ-004", "Vendor Payments Automation", "Finance", ProjectStatus.on_hold, 3, -150, 60, 210_000),
    ("PRJ-005", "Zero Trust Network Rollout", "Platform", ProjectStatus.active, 1, -90, 45, 640_000),
    ("PRJ-006", "HR Self-Service Refresh", "People", ProjectStatus.planning, 4, 15, 220, 150_000),
    ("PRJ-007", "Legacy CRM Decommission", "Operations", ProjectStatus.completed, 2, -400, -40, 280_000),
    ("PRJ-008", "Regulatory Reporting Uplift", "Finance", ProjectStatus.active, 1, -75, 20, 520_000),
]

# --- Standard delivery phases, chained so each waits on the previous one ---
DEMO_PHASES = [
    ("Discovery and requirements", 100.0, DeliverableStatus.completed),
    ("Solution design", 100.0, DeliverableStatus.completed),
    ("Build phase 1", 65.0, DeliverableStatus.in_progress),
    ("Integration testing", 20.0, DeliverableStatus.in_progress),
    ("Security review", 0.0, DeliverableStatus.blocked),
    ("Go-live and handover", 0.0, DeliverableStatus.not_started),
]

# --- Assignments as (project index, person index, percent, role).
#     Deliberately overlapping so some people end up over-allocated. ---
DEMO_ALLOCATIONS = [
    (0, 0, 60, "Tech lead"), (0, 3, 40, "Designer"), (0, 4, 30, "QA"),
    (1, 2, 80, "Data engineer"), (1, 1, 50, "Backend"), (1, 0, 30, "Tech lead"),
    (2, 7, 70, "Frontend"), (2, 3, 40, "Designer"), (2, 4, 40, "QA"),
    (3, 6, 50, "Analyst"), (3, 1, 30, "Backend"),
    (4, 5, 70, "DevOps"), (4, 8, 60, "Security"), (4, 0, 20, "Tech lead"),
    (5, 6, 30, "Analyst"), (5, 9, 40, "Product owner"),
    (7, 2, 40, "Data engineer"), (7, 9, 60, "Product owner"), (7, 8, 50, "Security"),
]

# --- Fraction of each project's budget already spent. PRJ-007 exceeds 1.0
#     on purpose, to give the budget page an overspend to show. ---
DEMO_BURN_RATES = {0: 0.72, 1: 0.94, 2: 0.31, 3: 0.55, 4: 0.68, 5: 0.05, 6: 1.02, 7: 0.88}

SPEND_CATEGORIES = ["labour", "software", "cloud", "vendor", "travel"]


def run() -> None:
    """Wipe the tables and rebuild the demo portfolio."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    random.seed(7)  # same demo data every run

    try:
        _clear_existing(db)
        users = _create_users(db)
        resources = _create_resources(db)
        projects = _create_projects(db, users)
        _create_deliverables(db, projects, resources)
        _create_allocations(db, projects, resources)
        _create_budget_entries(db, projects)
        _print_credentials()
    finally:
        db.close()


def _clear_existing(db) -> None:
    """Delete children before parents so foreign keys never block the wipe."""
    for model in (BudgetEntry, Allocation, Deliverable, Project, Resource, User):
        db.query(model).delete()
    db.commit()


def _create_users(db) -> list[User]:
    users = [
        User(
            email=email,
            full_name=name,
            role=role,
            hashed_password=hash_password(password),
        )
        for email, name, role, password in DEMO_USERS
    ]
    db.add_all(users)
    db.commit()
    for user in users:
        db.refresh(user)
    return users


def _create_resources(db) -> list[Resource]:
    resources = [
        Resource(
            full_name=name,
            email=f"{name.split()[0].lower()}.{name.split()[1].lower()}@acme.com",
            job_title=title,
            department=department,
            location=location,
            weekly_capacity_hours=capacity,
        )
        for name, title, department, location, capacity in DEMO_PEOPLE
    ]
    db.add_all(resources)
    db.commit()
    for resource in resources:
        db.refresh(resource)
    return resources


def _create_projects(db, users: list[User]) -> list[Project]:
    admin, manager = users[0], users[1]

    projects = [
        Project(
            code=code,
            name=name,
            description=f"{name} for the {department} department.",
            department=department,
            status=status,
            priority=priority,
            start_date=TODAY + timedelta(days=start_offset),
            end_date=TODAY + timedelta(days=end_offset),
            planned_budget=budget,
            # High priority work goes to the dedicated manager account.
            manager_id=manager.id if priority <= 2 else admin.id,
        )
        for code, name, department, status, priority, start_offset, end_offset, budget
        in DEMO_PROJECTS
    ]
    db.add_all(projects)
    db.commit()
    for project in projects:
        db.refresh(project)
    return projects


def _create_deliverables(db, projects: list[Project], resources: list[Resource]) -> None:
    """Build a chain per project: each phase depends on the one before it."""
    for project in projects:
        previous = None

        for index, (label, pct, status) in enumerate(DEMO_PHASES):
            # Completed projects have everything done; planning projects have
            # barely started. Everything else uses the standard mix.
            if project.status == ProjectStatus.completed:
                pct, status = 100.0, DeliverableStatus.completed
            elif project.status == ProjectStatus.planning and index > 1:
                pct, status = 0.0, DeliverableStatus.not_started

            deliverable = Deliverable(
                project_id=project.id,
                name=label,
                description=f"{label} for {project.name}.",
                status=status,
                completion_pct=pct,
                due_date=project.start_date + timedelta(days=(index + 1) * 25),
                owner_id=random.choice(resources).id,
                depends_on_id=previous.id if previous else None,
            )
            db.add(deliverable)
            db.commit()
            db.refresh(deliverable)
            previous = deliverable


def _create_allocations(db, projects: list[Project], resources: list[Resource]) -> None:
    for project_index, resource_index, percent, role_name in DEMO_ALLOCATIONS:
        project = projects[project_index]
        db.add(
            Allocation(
                project_id=project.id,
                resource_id=resources[resource_index].id,
                allocation_pct=percent,
                role_on_project=role_name,
                start_date=project.start_date,
                end_date=project.end_date,
            )
        )
    db.commit()


def _create_budget_entries(db, projects: list[Project]) -> None:
    """Spread each project's spend across six monthly entries."""
    months = 6

    for index, project in enumerate(projects):
        target_total = project.planned_budget * DEMO_BURN_RATES.get(index, 0.5)

        for month in range(months):
            db.add(
                BudgetEntry(
                    project_id=project.id,
                    category=SPEND_CATEGORIES[month % len(SPEND_CATEGORIES)],
                    amount=round(target_total / months, 2),
                    entry_date=TODAY - timedelta(days=30 * (months - month)),
                    description=f"Month {month + 1} spend",
                )
            )
    db.commit()


def _print_credentials() -> None:
    print("Seed complete.")
    print("  admin@acme.com   / Admin@123    (full access)")
    print("  manager@acme.com / Manager@123  (can edit projects, not users)")
    print("  viewer@acme.com  / Viewer@123   (read only)")


if __name__ == "__main__":
    run()
