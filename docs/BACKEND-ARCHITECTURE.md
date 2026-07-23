# Backend architecture

The backend follows a layered architecture. Each layer depends only on the
ones below it, so a change in one place does not ripple through the rest.

```
   HTTP request
        │
        ▼
┌───────────────────┐
│   api/            │  Routes. Parse the request, call a service, return.
│                   │  No business rules. No queries.
└─────────┬─────────┘
          │  DTOs in, DTOs out
          ▼
┌───────────────────┐
│   services/       │  Business rules. Risk scoring, capacity, validation.
│                   │  Knows nothing about HTTP.
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│   repositories/   │  Every SQLAlchemy query in the application.
│                   │  The only layer that touches the session.
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│   models/         │  ORM entities mapped to database tables.
└───────────────────┘

   core/   config, security, dependencies, exceptions  (used by all layers)
   dto/    request and response shapes crossing the API boundary
   db/     engine, session factory, declarative base
   seeds/  demo data
```

---

## Package by package

```
backend/
├── lambda_handler.py            AWS Lambda entry point (Mangum adapter)
├── requirements.txt
└── app/
    ├── main.py                  Creates the FastAPI app, mounts the router
    │
    ├── core/                    Cross-cutting concerns
    │   ├── config.py            All settings, read from environment or .env
    │   ├── security.py          Password hashing, JWT encode and decode
    │   ├── dependencies.py      get_current_user, require_admin, require_editor
    │   └── exceptions.py        AppError and its subclasses
    │
    ├── db/
    │   ├── base.py              The declarative Base
    │   └── session.py           Engine, SessionLocal, get_db dependency
    │
    ├── models/                  One file per table
    │   ├── enums.py             Role, ProjectStatus, DeliverableStatus
    │   ├── user.py
    │   ├── resource.py
    │   ├── project.py
    │   ├── deliverable.py
    │   ├── allocation.py
    │   └── budget_entry.py
    │
    ├── dto/                     One file per domain area
    │   ├── common_dto.py        Shared config and helpers
    │   ├── auth_dto.py
    │   ├── user_dto.py
    │   ├── resource_dto.py
    │   ├── project_dto.py
    │   ├── deliverable_dto.py
    │   ├── allocation_dto.py
    │   ├── budget_dto.py
    │   └── analytics_dto.py
    │
    ├── repositories/            One file per entity
    │   ├── base_repository.py   Generic CRUD the others inherit
    │   ├── user_repository.py
    │   ├── resource_repository.py
    │   ├── project_repository.py
    │   ├── deliverable_repository.py
    │   ├── allocation_repository.py
    │   └── budget_repository.py
    │
    ├── services/                One file per domain area
    │   ├── auth_service.py
    │   ├── user_service.py
    │   ├── resource_service.py
    │   ├── project_service.py   Contains the risk scoring rules
    │   ├── deliverable_service.py   Contains the dependency chain builder
    │   ├── allocation_service.py    Contains the over-allocation rules
    │   ├── budget_service.py
    │   └── analytics_service.py     Composes the others; no queries of its own
    │
    ├── api/
    │   ├── router.py            Assembles every route module
    │   └── v1/                  One file per domain area
    │       ├── auth_routes.py
    │       ├── user_routes.py
    │       ├── project_routes.py
    │       ├── deliverable_routes.py
    │       ├── resource_routes.py
    │       ├── allocation_routes.py
    │       ├── budget_routes.py
    │       └── analytics_routes.py
    │
    └── seeds/
        └── seed_data.py         Demo portfolio
```

---

## Why each boundary exists

**Routes are thin.** A route parses the request, calls one service method, and
returns the result. Look at `project_routes.py` — no route body is more than
three lines. If a route starts growing an `if`, that logic belongs in a service.

**Services never import FastAPI.** They raise `NotFoundError`, `ConflictError`
and friends from `core/exceptions.py`. A single handler in `main.py` turns
those into HTTP responses. That means the same service could be called from a
CLI script, a scheduled job, or a test, with no web server involved.

**Repositories own every query.** Nothing outside `repositories/` writes
`db.query(...)`. Swapping the database, adding caching, or logging slow queries
would touch one package.

**DTOs are not models.** The ORM `User` has `hashed_password`; the
`UserResponse` DTO does not. Because they are separate, the database schema can
change without altering the API contract, and the API can hide fields the
database holds.

**Enums live alone.** `models/enums.py` is imported by both the models and the
DTOs. If they were defined in `models/user.py`, the DTO package would depend on
the ORM package, and the layering would leak.

---

## Where to make a change

| You want to... | Edit |
|---|---|
| Change what counts as an at-risk project | `services/project_service.py` → `_assess_risk` |
| Change the over-allocation threshold | `services/allocation_service.py` → `find_over_allocated` |
| Add a filter to the project list | `repositories/project_repository.py` → `search`, then the route |
| Add a field to a project | `models/project.py`, then `dto/project_dto.py` |
| Add a new endpoint | New method in the service, new route in `api/v1/` |
| Add a whole new entity | model → repository → dto → service → routes → register in `api/router.py` |
| Change who can do what | `core/dependencies.py` |
| Change the demo data | `seeds/seed_data.py` |

The order in that last row is worth remembering: build bottom-up, because each
layer only needs the one beneath it to already exist.

---

## Adding a feature, worked example

Say you want a `client_name` on projects.

1. **Model** — add `client_name = Column(String(160))` to `models/project.py`.
2. **DTO** — add `client_name: Optional[str] = None` to `ProjectBase` and
   `ProjectUpdateRequest` in `dto/project_dto.py`.
3. **Service and repository** — nothing to do. They pass fields through
   generically, so a new column needs no code.
4. **Route** — nothing to do, for the same reason.
5. **Frontend** — add the field to the form in `pages/Projects.jsx`.

Two files for a new field. That is the payoff of the layering.

---

## Known simplifications

Named deliberately, because knowing the limits of your own design is worth more
than pretending there are none.

- **Tables are created at startup** rather than with Alembic migrations. Fine
  for a workshop, wrong for production, where schema changes need to be
  versioned and reversible.
- **Services construct their own repositories.** A larger system would inject
  them, making it possible to swap in a fake repository for unit tests without
  a database.
- **No caching.** `calculate_metrics` runs on every read. Correct, and fast
  enough at this scale, but on thousands of projects it would need caching or a
  materialised view.
- **No test suite yet.** `services/project_service.py` is the highest-value
  place to start, because that is where the business rules live and they need
  no database to test.
