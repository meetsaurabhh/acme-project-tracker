# Project walkthrough

Everything in one place: what this application is, what each file does, and how
it satisfies the workshop brief. Read this before a demo.

---

## Part 1 — What problem this solves

ACME runs projects across several departments. The information exists, but it
is scattered: schedules in one place, spend in another, who-is-working-on-what
in a third. Nobody can see the whole picture, so problems are found late.

The brief lists seven questions the company cannot currently answer. This
platform answers all seven from one database.

**The core idea worth understanding:** the application does not store a project
status that somebody types in. It *calculates* health from the underlying facts
every time you look. A manager cannot mark a failing project green, because
nobody sets the colour — the data does.

That single decision is what makes this a tracking tool rather than a
spreadsheet with a login.

---

## Part 2 — How the three pieces fit together

```
   Browser (React + Material UI)          localhost:3030
        │
        │  HTTP requests carrying a token
        ▼
   FastAPI backend (Python)               localhost:8000
        │
        │  SQL through SQLAlchemy
        ▼
   PostgreSQL                             localhost:5432
```

The browser never touches the database. Every rule — who may edit, what counts
as at-risk, how budget burn is worked out — lives in the backend, where it
cannot be bypassed by editing the page in developer tools.

---

## Part 3 — One request, traced end to end

Worth memorising. If an assessor asks "walk me through what happens when you
click a project", this is the answer.

**You click a project on the dashboard.**

1. `frontend/src/pages/ProjectDetail.jsx` calls `api.get('/api/projects/3')`.
2. `frontend/src/api.js` attaches the saved token to the request header.
3. `backend/app/api/v1/project_routes.py` receives it. Before the route body
   runs, `get_current_user` in `core/dependencies.py` decodes the token and
   loads the user. No valid token, no response.
4. The route calls `ProjectService.get_project(3)`. That is the whole route
   body — three lines.
5. `services/project_service.py` asks `ProjectRepository` for project 3, then
   asks `DeliverableRepository` and `BudgetRepository` for its deliverables and
   spend.
6. `repositories/` runs the actual SQL. Nothing else in the application does.
7. Back in the service, `calculate_metrics` works out progress, budget burn,
   time elapsed, and runs the six risk checks.
8. The result is packed into a `ProjectResponse` DTO — which deliberately has
   no `hashed_password` field, because DTOs are separate from ORM models.
9. FastAPI serialises it to JSON. React renders it.

Five layers, each one only knowing about the layer below.

---

## Part 4 — Every backend file

### `app/main.py` — the entry point
Creates the FastAPI application, enables CORS so the browser on port 3030 may
call port 8000, registers the error handler that converts service exceptions
into HTTP responses, and mounts every route. Contains no business logic.

### `app/core/` — cross-cutting concerns

| File | What it does |
|---|---|
| `config.py` | Every setting in one class. Reads `.env`. Change the database or the token lifetime here, nowhere else. |
| `security.py` | Password hashing and JWT creation/decoding. Pure functions — no HTTP, no database. |
| `dependencies.py` | `get_current_user` identifies the caller from their token. `require_admin` and `require_editor` enforce roles. **This is where access control actually happens.** |
| `exceptions.py` | `NotFoundError`, `ConflictError`, `AuthorizationError` and friends. Services raise these instead of HTTP errors, which is what keeps the business layer independent of FastAPI. |

### `app/db/` — database plumbing

| File | What it does |
|---|---|
| `base.py` | The `Base` class every ORM model inherits. |
| `session.py` | The engine, the session factory, and `get_db` — which opens a session per request and always closes it. |

### `app/models/` — the database tables

One file per table. These *are* the schema; SQLAlchemy creates the real tables
from them.

| File | Represents |
|---|---|
| `enums.py` | The fixed choice lists: roles, project statuses, deliverable statuses. In their own file so both models and DTOs can use them without depending on each other. |
| `user.py` | Someone who can sign in. Stores a password *hash*, never a password. |
| `resource.py` | Someone who does the work. Separate from User on purpose — a contractor may never log in, and a sponsor may log in but never take an assignment. |
| `project.py` | Code, name, department, status, dates, planned budget, owning manager. |
| `deliverable.py` | A piece of work inside a project. The `depends_on_id` column points at another deliverable — that single self-referencing column is what builds the whole dependency chain. |
| `allocation.py` | Links a person to a project with a percentage of their week. A unique constraint stops the same person being added twice. |
| `budget_entry.py` | One line of money actually spent. Stored as individual entries, not a running total, so the system can say *where* the money went and *when*. |

### `app/dto/` — the API contract

DTOs define what data may come in and what goes out. They are separate from the
models for two reasons: the database schema can change without breaking the
API, and the API can hide fields the database holds.

Each file follows the same pattern:
- `XBase` — fields common to everything
- `XCreateRequest` — what you send to create one
- `XUpdateRequest` — every field optional, so you can change one thing
- `XResponse` — what comes back, including calculated fields

`project_dto.py` is the interesting one: `ProjectResponse` carries
`completion_pct`, `risk_level` and `risk_reasons`, none of which exist in the
database. They are worked out at read time.

### `app/repositories/` — every database query

| File | What it does |
|---|---|
| `base_repository.py` | Generic get, list, create, update, delete that the others inherit. |
| `user_repository.py` | Plus `get_by_email`, used on every authenticated request. |
| `project_repository.py` | Plus `search` with filters, and `list_departments` for the dropdown. |
| `deliverable_repository.py` | Plus `clear_dependents`, which unhooks anything waiting on a deliverable before it is deleted. |
| `allocation_repository.py` | Plus `find_pairing`, which enforces one assignment per person per project. |
| `budget_repository.py` | Plus `total_for_project`, which sums *in the database* so one row comes back instead of every spend line. |

**No file outside this package writes a database query.** That is the rule that
makes the layer worth having.

### `app/services/` — the business rules

This is where the thinking happens.

**`project_service.py`** — the most important file in the project. Contains
`_assess_risk`, which runs six independent checks on every open project:

1. Past its end date and not complete
2. Schedule used exceeds work delivered by 20 points or more
3. 90%+ of budget spent while under 75% delivered
4. A deliverable is explicitly blocked
5. Deliverables are past their own due dates
6. The project is on hold

One check firing means **watch**. Two or more means **at risk**. The reasons
are returned with the verdict, so the dashboard explains itself instead of
showing an unexplained red dot.

**`deliverable_service.py`** — contains `get_dependency_chain`, which walks the
`depends_on_id` links depth-first and returns a flat list where each item
carries a `depth` so the UI can indent it, and a flag for whether the thing it
waits on is still unfinished. It also guards against circular references:
anything the walk cannot reach is appended rather than looping forever.

**`allocation_service.py`** — contains `find_over_allocated`. Adds up each
person's commitments across *live* projects only, because completed and
cancelled work releases its people. Anything over 100% means that person is
promised to more work than their week contains.

**`resource_service.py`** — per-person utilisation. Capacity is stored per
person in hours, so a part-time colleague on 32 hours is correctly treated as
full at 100%, not at 40 hours' worth of work.

**`analytics_service.py`** — the dashboard figures. Note that it *composes the
other services* rather than querying directly, so the risk rules and capacity
rules exist in exactly one place each.

**`auth_service.py`** — sign-in. Returns the same message whether the email is
unknown or the password is wrong, so the response cannot be used to discover
which emails are registered.

**`user_service.py`**, **`budget_service.py`** — account management and spend.

### `app/api/v1/` — the HTTP routes

Eight files, one per area. Every route body is two or three lines: parse the
request, call a service, return the result. If a route grows an `if`, that
logic belongs in a service.

`router.py` assembles all eight into one object that `main.py` mounts.

### `app/seeds/seed_data.py`
Loads the demo portfolio: 3 accounts, 10 people, 8 projects, 48 deliverables
with real dependency chains, 19 assignments, and six months of spend. Dates are
stored as offsets from today, so the data stays current whenever you load it.

---

## Part 5 — Every frontend file

| File | What it does |
|---|---|
| `main.jsx` | Starts React, applies the theme. |
| `App.jsx` | Every route. `Protected` redirects signed-out users to login and keeps non-admins out of `/users`. |
| `auth.jsx` | Holds who is signed in. Exposes `canEdit` and `isAdmin`, which the pages use to hide buttons. |
| `api.js` | One axios instance. Attaches the token to every request; on a 401, clears it and bounces to login. |
| `theme.js` | All colours and fonts in one place. |
| `components/Layout.jsx` | Sidebar and page frame. **Uses `react-responsive`** — on screens under 900px the sidebar becomes a hamburger drawer. |
| `components/DeliveryRail.jsx` | The signature visual. Two tracks on the same scale: schedule used above, work delivered below. The gap between them *is* the slippage. |
| `components/RiskChip.jsx` | The coloured health label. |
| `pages/Login.jsx` | Sign-in screen. |
| `pages/Dashboard.jsx` | Portfolio summary, flagged projects with reasons, over-allocated people. |
| `pages/Projects.jsx` | List with search and three filters, plus create/edit/delete. |
| `pages/ProjectDetail.jsx` | Four tabs: dependency chain, deliverables, team, spend. |
| `pages/Resources.jsx` | Everyone's load, with a bar per person. |
| `pages/Budget.jsx` | Planned versus consumed per project. |
| `pages/Users.jsx` | Account management. Admin only. |

---

## Part 6 — How the brief is satisfied

### The seven business questions

| # | Question | Where | Endpoint |
|---|---|---|---|
| 1 | Current status of each active project | Projects page | `GET /api/projects?status=active` |
| 2 | Which projects are at risk | Dashboard, top table | `GET /api/analytics/at-risk` |
| 3 | How resources are allocated | People page | `GET /api/analytics/resource-utilisation` |
| 4 | Key deliverables and completion | Project → Deliverables tab | `GET /api/deliverables?project_id=3` |
| 5 | Who is over-allocated | Dashboard, lower panel | `GET /api/analytics/over-allocated` |
| 6 | Dependency chain between deliverables | Project → Dependency chain tab | `GET /api/projects/3/dependency-chain` |
| 7 | Budget consumed versus planned | Budget page | `GET /api/analytics/budget` |

### The five required features

| Requirement | How it is met |
|---|---|
| User authentication and authorisation | JWT tokens. Passwords stored as pbkdf2 hashes, never plain text. |
| Role-based access control | Three roles enforced in `core/dependencies.py`. The frontend hides buttons too, but the backend is what actually stops you. |
| CRUD for projects, deliverables, resources, budget | All four, full create/read/update/delete. 35 endpoints. |
| Search and filter | Projects by text, status, department and health. People by name, title, department. Deliverables by project, status, text, overdue. |
| Responsive design | `react-responsive` swaps tables for cards under 900px and collapses the sidebar. |

### The technology stack

| Required | Used | Where to point |
|---|---|---|
| HTML | `frontend/index.html` |
| CSS | `theme.js` plus MUI's `sx` styling |
| React.js | Every `.jsx` file |
| **React Responsive** | `useMediaQuery` in `Layout.jsx`, `Dashboard.jsx`, `Projects.jsx`, `Budget.jsx` |
| **Material UI** | `AppBar`, `Drawer`, `Table`, `Dialog`, `Chip`, `Grid` throughout |
| Python | FastAPI backend, 59 files |
| PostgreSQL | Six tables, accessed via SQLAlchemy |

### The "good to know" list

| Item | Where |
|---|---|
| Git, GitHub | Your repository, with commit history |
| Terraform | `infra/terraform/main.tf` (real AWS: S3, CloudFront, RDS) and `infra/localstack/main.tf` |
| Shell scripts | `scripts/` — setup, reset, deploy |
| AWS Serverless | `lambda_handler.py` wraps the API for Lambda; Terraform provisions S3, API Gateway and RDS |

---

## Part 7 — What to say in a demo

Four points that show you understood the design rather than assembled it.

**1. Health is calculated, not stored.**
"There's no status field a manager can set to green. The six checks run against
the underlying dates, spend and deliverables every time you load the page. And
because the reasons come back with the verdict, the dashboard tells you *why*
something is flagged, not just that it is."

**2. The layers have a rule, and the rule is enforced.**
"Routes call services, services call repositories, repositories touch the
database. No SQL query exists outside `repositories/`, and no service imports
FastAPI. That's why the risk logic could be called from a scheduled job or a
test with no web server involved."

**3. Access control is server-side.**
"The frontend hides buttons a viewer can't use, but that's cosmetic. Sign in as
viewer, open the API docs, and try to POST a project — you get a 403 naming
your role. The dependency in `core/dependencies.py` is what actually stops you."

**4. Know your own limits.**
"Tables are created at startup rather than through Alembic migrations, which is
fine for a workshop and wrong for production. `calculate_metrics` runs on every
read with no caching — correct, and fast enough at this scale, but it would need
a materialised view at thousands of projects. And there are no tests yet;
`project_service.py` is where I'd start, because the rules there need no
database to test."

That last point is the one that separates a good demo from a great one.
Assessors ask what you'd do differently. Having a specific, technically sound
answer ready is worth more than pretending the design is perfect.

---

## Part 8 — The live demo sequence

Ten minutes, in this order:

1. **Dashboard.** Explain the two-track bars. Point at a flagged project and
   read its reasons aloud.
2. **Click into that project.** Show the dependency chain — point out an item
   marked "waiting on predecessor" and explain that's the bottleneck.
3. **People page.** Show someone over 100% and name the projects competing for
   them.
4. **Budget page.** Show a project where spend has outrun delivery.
5. **Create a project.** Then open pgAdmin and show the new row in the
   `projects` table. That proves the whole stack in one move.
6. **Sign out, sign in as viewer.** Every edit button is gone.
7. **Open `/docs`.** Show the 35 endpoints, then use "Try it out" on
   `/api/analytics/at-risk` to show the raw JSON behind the dashboard.
8. **Resize the browser window.** The sidebar collapses, tables become cards.
   That's React Responsive doing its job.
