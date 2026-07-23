# ACME Project Tracker

A working project management and tracking platform, built for the Citi coding
workshop scenario. React + Material UI on the front, Python (FastAPI) on the
back, PostgreSQL underneath.

This guide assumes you have never set any of this up before. Follow it in
order and you will have the app running in about fifteen minutes.

---

## 1. What you are about to run

Three pieces talk to each other:

| Piece | What it does | Where you see it |
|---|---|---|
| **Frontend** (React + Material UI) | The screens you click on | http://localhost:3030 |
| **Backend** (Python / FastAPI) | The rules and the maths | http://localhost:8000/docs |
| **Database** (PostgreSQL) | Where the data actually lives | port 5432 |

The frontend never touches the database. It asks the backend, and the backend
asks the database. That separation is the point of the exercise.

---

## 2. Install the one tool you need

**Docker Desktop** runs all three pieces for you, so you don't have to install
Python, Node and PostgreSQL separately.

1. Download it from https://www.docker.com/products/docker-desktop
2. Install it and **open it**. Wait until the whale icon says "Docker Desktop
   is running."

To check it worked, open a terminal and run:

```bash
docker --version
```

If you see a version number, you are ready. (On Windows, use PowerShell or
Git Bash as your terminal.)

---

## 3. Start everything

From inside this folder:

```bash
./scripts/setup.sh
```

On Windows PowerShell, run these three lines instead:

```powershell
docker compose up -d --build
Start-Sleep -Seconds 25
docker compose exec -T backend python -m app.seeds.seed_data
```

The first run takes a few minutes because it downloads the base images. When
it finishes you will see the demo login details printed.

---

## 4. Open the app

Go to **http://localhost:3030** and sign in:

| Email | Password | What they can do |
|---|---|---|
| admin@acme.com | `Admin@123` | Everything, including managing accounts |
| manager@acme.com | `Manager@123` | Create and edit projects, deliverables, people, spend |
| viewer@acme.com | `Viewer@123` | Read only — buttons to change things are hidden |

Sign in as each of the three to see role-based access control working. That is
a requirement in the brief, and it is easiest to demo by switching accounts.

Also open **http://localhost:8000/docs**. That is the auto-generated API
documentation — every endpoint, clickable, with a "Try it out" button. It is
worth showing in a demo.

---

## 5. What to click first

1. **Dashboard** — the portfolio at a glance. The bars are the signature idea
   in this app: the thin line on top is *how much of the schedule has been
   used*, the thick bar below is *how much has actually been delivered*. The
   gap between them is the slippage. You can spot a failing project without
   reading a number.
2. **Projects** — search, filter by status/department/health, and create a new
   one. Click any row to open it.
3. Inside a project — four tabs: the **dependency chain** (each deliverable
   indented under the one it waits on), **deliverables**, **team**, and
   **spend**.
4. **People** — everyone's total commitment across live projects. Anyone above
   100% is flagged in red.
5. **Budget** — planned versus consumed, per project.

---

## 6. Useful commands

```bash
docker compose ps            # what is running
docker compose logs -f backend   # watch the backend logs
docker compose down          # stop everything (data survives)
docker compose down -v       # stop and wipe the database completely
./scripts/reset-db.sh        # reload the demo data
```

If something breaks, `docker compose logs backend` almost always tells you
why.

---

## 7. Running it without Docker

Only do this if Docker is not an option. You will need Python 3.11+, Node 18+
and a local PostgreSQL.

**Backend**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export DATABASE_URL="postgresql+psycopg2://acme:acme@localhost:5432/acme_pm"
python -m app.seeds.seed_data
uvicorn app.main:app --reload
```

**Frontend** (in a second terminal)

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

---

## 8. How the answers are calculated

Every business question in the brief maps to a real endpoint. See
[docs/BUSINESS-QUESTIONS.md](./docs/BUSINESS-QUESTIONS.md) for the full
mapping, and [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md) for how the code is
laid out.

The one thing worth understanding before you present: **a project is flagged
when two or more warning signs fire at once.** The signs are past its end date,
schedule ahead of delivery by 20 points or more, budget burn ahead of delivery,
a blocked deliverable, overdue deliverables, or being on hold. One sign means
"watch", two or more means "at risk". The dashboard shows you which signs
fired, so nothing is a black box.

---

## 9. Deploying to AWS

`infra/terraform/main.tf` provisions S3 + CloudFront for the frontend and RDS
PostgreSQL for the database.

```bash
cd infra/terraform
terraform init
terraform apply -var="db_password=SomethingStrong123"
```

Then push the built frontend up:

```bash
./scripts/deploy.sh <bucket-name-from-output> <distribution-id-from-output>
```

The backend on Lambda is the one piece left deliberately unfinished — wrap
`app.main:app` with [Mangum](https://mangum.io) and package it as a Lambda
function behind API Gateway. It is a good extension task if you have time.

---

## 10. Ideas if you want to go further

- Export the portfolio view to CSV
- Email or Slack alerts when a project crosses into "at risk"
- Audit trail of who changed what
- Gantt view built on the dependency chain data that is already there
- Unit tests with pytest for the risk-scoring rules in `backend/app/services/project_service.py`

---

## Project layout

```
acme-pm/
├── backend/                    Python API (layered architecture)
│   └── app/
│       ├── main.py                 creates the app, mounts the router
│       ├── api/                    HTTP routes only
│       ├── services/               business rules
│       ├── repositories/           every database query
│       ├── models/                 ORM entities
│       ├── dto/                    request and response shapes
│       ├── core/                   config, security, dependencies, errors
│       ├── db/                     engine and session
│       └── seeds/                  demo data
├── frontend/                   React app
│   └── src/
│       ├── pages/                  one file per screen
│       ├── components/             shared UI pieces
│       ├── api.js                  talks to the backend
│       ├── auth.jsx                keeps track of who is signed in
│       └── theme.js                colours and typography
├── infra/terraform/            AWS infrastructure
├── infra/localstack/           LocalStack infrastructure
├── scripts/                    setup, reset and deploy
└── docker-compose.yml          runs all three pieces together
```
