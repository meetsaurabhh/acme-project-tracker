# Architecture

## The shape of the system

```
Browser
   │  React + Material UI (port 3030)
   │  axios attaches a JWT to every request
   ▼
FastAPI  (port 8000)
   │  checks the token, checks the role, runs the rules
   ▼
PostgreSQL (port 5432)
```

Nothing in the browser talks to the database. Every rule — who may edit, what
counts as at-risk, how budget burn is calculated — lives in the backend, where
it cannot be bypassed by editing the page in dev tools.

---

## Data model

```
User            people who can sign in (admin / manager / viewer)
Resource        people who do the work (may never sign in)
Project         code, dates, planned budget, owning manager
Deliverable     belongs to a project, may depend on one other deliverable
Allocation      links a Resource to a Project with a percentage
BudgetEntry     one line of actual spend against a project
```

**Why User and Resource are separate.** A contractor is a resource with no
login. An executive sponsor is a login with no allocation. Merging them looks
tidier on day one and hurts on day thirty.

**Why `depends_on_id` sits on Deliverable.** A single self-referencing column
gives a tree, which covers the "what waits on what" question without the
complexity of a full dependency graph table. If the workshop asks for
many-to-many dependencies later, that becomes a join table.

**Why spend is a list of entries rather than a single number.** A running total
tells you the burn. A list of entries tells you the burn *and* where it went
and when, which is what a project manager actually needs in a steering meeting.

---

## Authentication and roles

Sign-in returns a JSON Web Token that the browser stores and sends back on
every request. The token carries the email and role; the backend re-reads the
user from the database on each request so a deactivated account stops working
immediately rather than when the token expires.

Three roles, enforced by FastAPI dependencies in `core/dependencies.py`:

| Role | Read | Create/edit projects, deliverables, people, spend | Manage accounts |
|---|---|---|---|
| admin | yes | yes | yes |
| manager | yes | yes | no |
| viewer | yes | no | no |

The frontend also hides buttons a role cannot use, but that is only for
tidiness. The backend is the thing that actually enforces it.

---

## Where to change things

| You want to... | Edit this |
|---|---|
| Change the at-risk rules | `backend/app/services/project_service.py` → `_assess_risk` |
| Add a field to a project | `models/project.py`, then `dto/project_dto.py`, then the form in `frontend/src/pages/Projects.jsx` |
| Add a new screen | new file in `frontend/src/pages/`, add a route in `App.jsx`, add a link in `components/Layout.jsx` |
| Change colours or fonts | `frontend/src/theme.js` |
| Change the demo data | `backend/app/seeds/seed_data.py`, then rerun the seed |

---

## Known simplifications

These are deliberate, and worth naming out loud in a demo rather than hiding:

- Tables are created automatically at startup instead of using Alembic
  migrations. Fine for a workshop, wrong for production.
- The seed script clears the tables before loading. Do not point it at
  anything you care about.
- The JWT secret is in `docker-compose.yml` as plain text. In AWS it belongs in
  Secrets Manager.
- There are no automated tests yet. `services/project_service.py` is the
  highest-value place to add them, because that is where the business rules live.

For the full package-by-package breakdown, see
[BACKEND-ARCHITECTURE.md](./BACKEND-ARCHITECTURE.md).
