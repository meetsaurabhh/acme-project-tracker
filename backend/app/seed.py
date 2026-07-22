"""Fill an empty database with a realistic demo portfolio.

Run it with:  python -m app.seed
Safe to run twice: it clears the tables first.
"""

import random
from datetime import date, timedelta

from .database import Base, SessionLocal, engine
from .models import (
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
from .security import hash_password

TODAY = date.today()


def run():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Clear in dependency order.
        for model in (BudgetEntry, Allocation, Deliverable, Project, Resource, User):
            db.query(model).delete()
        db.commit()

        # ---------------- Users ----------------
        users = [
            User(
                email="admin@acme.com",
                full_name="Ada Okonkwo",
                role=Role.admin,
                hashed_password=hash_password("Admin@123"),
            ),
            User(
                email="manager@acme.com",
                full_name="Ravi Deshpande",
                role=Role.manager,
                hashed_password=hash_password("Manager@123"),
            ),
            User(
                email="viewer@acme.com",
                full_name="Sofia Marin",
                role=Role.viewer,
                hashed_password=hash_password("Viewer@123"),
            ),
        ]
        db.add_all(users)
        db.commit()
        for u in users:
            db.refresh(u)
        admin, manager, _viewer = users

        # ---------------- Resources ----------------
        people = [
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
        resources = [
            Resource(
                full_name=n,
                email=f"{n.split()[0].lower()}.{n.split()[1].lower()}@acme.com",
                job_title=t,
                department=d,
                location=loc,
                weekly_capacity_hours=cap,
            )
            for n, t, d, loc, cap in people
        ]
        db.add_all(resources)
        db.commit()
        for r in resources:
            db.refresh(r)

        # ---------------- Projects ----------------
        project_specs = [
            ("PRJ-001", "Customer Portal Rebuild", "Engineering", ProjectStatus.active, 1, -120, 30, 480000),
            ("PRJ-002", "Data Lake Migration", "Data", ProjectStatus.active, 1, -200, -10, 950000),
            ("PRJ-003", "Mobile Onboarding App", "Engineering", ProjectStatus.active, 2, -60, 120, 320000),
            ("PRJ-004", "Vendor Payments Automation", "Finance", ProjectStatus.on_hold, 3, -150, 60, 210000),
            ("PRJ-005", "Zero Trust Network Rollout", "Platform", ProjectStatus.active, 1, -90, 45, 640000),
            ("PRJ-006", "HR Self-Service Refresh", "People", ProjectStatus.planning, 4, 15, 220, 150000),
            ("PRJ-007", "Legacy CRM Decommission", "Operations", ProjectStatus.completed, 2, -400, -40, 280000),
            ("PRJ-008", "Regulatory Reporting Uplift", "Finance", ProjectStatus.active, 1, -75, 20, 520000),
        ]
        projects = []
        for code, name, dept, status, prio, start_off, end_off, budget in project_specs:
            projects.append(
                Project(
                    code=code,
                    name=name,
                    description=f"{name} for the {dept} department.",
                    department=dept,
                    status=status,
                    priority=prio,
                    start_date=TODAY + timedelta(days=start_off),
                    end_date=TODAY + timedelta(days=end_off),
                    planned_budget=budget,
                    manager_id=manager.id if prio <= 2 else admin.id,
                )
            )
        db.add_all(projects)
        db.commit()
        for p in projects:
            db.refresh(p)

        # ---------------- Deliverables (with dependency chains) ----------------
        phases = [
            ("Discovery and requirements", 100.0, DeliverableStatus.completed, -80),
            ("Solution design", 100.0, DeliverableStatus.completed, -55),
            ("Build phase 1", 65.0, DeliverableStatus.in_progress, -10),
            ("Integration testing", 20.0, DeliverableStatus.in_progress, 20),
            ("Security review", 0.0, DeliverableStatus.blocked, 35),
            ("Go-live and handover", 0.0, DeliverableStatus.not_started, 55),
        ]
        random.seed(7)
        for project in projects:
            previous = None
            for idx, (label, pct, status, due_off) in enumerate(phases):
                if project.status == ProjectStatus.completed:
                    pct, status = 100.0, DeliverableStatus.completed
                elif project.status == ProjectStatus.planning and idx > 1:
                    pct, status = 0.0, DeliverableStatus.not_started
                d = Deliverable(
                    project_id=project.id,
                    name=f"{label}",
                    description=f"{label} for {project.name}.",
                    status=status,
                    completion_pct=pct,
                    due_date=project.start_date + timedelta(days=(idx + 1) * 25 + due_off // 4),
                    owner_id=random.choice(resources).id,
                    depends_on_id=previous.id if previous else None,
                )
                db.add(d)
                db.commit()
                db.refresh(d)
                previous = d

        # ---------------- Allocations (deliberately creates over-allocation) ----------------
        allocation_plan = [
            (0, 0, 60, "Tech lead"), (0, 3, 40, "Designer"), (0, 4, 30, "QA"),
            (1, 2, 80, "Data engineer"), (1, 1, 50, "Backend"), (1, 0, 30, "Tech lead"),
            (2, 7, 70, "Frontend"), (2, 3, 40, "Designer"), (2, 4, 40, "QA"),
            (3, 6, 50, "Analyst"), (3, 1, 30, "Backend"),
            (4, 5, 70, "DevOps"), (4, 8, 60, "Security"), (4, 0, 20, "Tech lead"),
            (5, 6, 30, "Analyst"), (5, 9, 40, "Product owner"),
            (7, 2, 40, "Data engineer"), (7, 9, 60, "Product owner"), (7, 8, 50, "Security"),
        ]
        for p_idx, r_idx, pct, role_name in allocation_plan:
            db.add(
                Allocation(
                    project_id=projects[p_idx].id,
                    resource_id=resources[r_idx].id,
                    allocation_pct=pct,
                    role_on_project=role_name,
                    start_date=projects[p_idx].start_date,
                    end_date=projects[p_idx].end_date,
                )
            )
        db.commit()

        # ---------------- Budget entries ----------------
        categories = ["labour", "software", "cloud", "vendor", "travel"]
        burn = {0: 0.72, 1: 0.94, 2: 0.31, 3: 0.55, 4: 0.68, 5: 0.05, 6: 1.02, 7: 0.88}
        for idx, project in enumerate(projects):
            target = project.planned_budget * burn.get(idx, 0.5)
            months = 6
            for m in range(months):
                db.add(
                    BudgetEntry(
                        project_id=project.id,
                        category=categories[m % len(categories)],
                        amount=round(target / months, 2),
                        entry_date=TODAY - timedelta(days=30 * (months - m)),
                        description=f"Month {m + 1} spend",
                    )
                )
        db.commit()

        print("Seed complete.")
        print("  admin@acme.com   / Admin@123    (full access)")
        print("  manager@acme.com / Manager@123  (can edit projects, not users)")
        print("  viewer@acme.com  / Viewer@123   (read only)")
    finally:
        db.close()


if __name__ == "__main__":
    run()
