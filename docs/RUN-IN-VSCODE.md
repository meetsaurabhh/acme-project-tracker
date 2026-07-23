# Running the project in VS Code on a VDI

Your VDI is just another Windows machine. The code is identical — only the way
you start it changes.

---

## Part 1: Get the code onto the VDI

Copy-paste between your laptop and a VDI is usually blocked, and dragging a zip
across often is too. Use Git — it is in the workshop tech stack anyway, so you
get credit for it.

### On your own laptop, once

```powershell
cd C:\Users\LENOVO\Desktop\acme-pm

git init
git add .
git commit -m "ACME project tracker: initial working version"
```

Then create an empty repository on https://github.com/new (name it
`acme-project-tracker`, leave "Add a README" unticked) and run the two lines
GitHub shows you:

```powershell
git remote add origin https://github.com/YOUR-USERNAME/acme-project-tracker.git
git branch -M main
git push -u origin main
```

### On the VDI

```powershell
cd C:\Users\YOURNAME\Documents
git clone https://github.com/YOUR-USERNAME/acme-project-tracker.git
cd acme-project-tracker
code .
```

`code .` opens the folder in VS Code. If the command isn't recognised, open VS
Code manually → **File → Open Folder** → pick the folder.

> If GitHub is blocked on the VDI, ask whether there is an internal GitHub
> Enterprise or Bitbucket. Failing that, a zip on a shared network drive works.

---

## Part 2: Find out what the VDI has

Open the VS Code terminal with `` Ctrl + ` `` and run:

```powershell
python --version
node --version
docker --version
```

| Result | What to do |
|---|---|
| All three answer, and Docker Desktop actually starts | Use Route A |
| Python and Node answer, Docker does not | Use Route B |
| Node is missing | Install Node from https://nodejs.org, then Route B |
| Python is missing | Install Python 3.12 from https://python.org (tick "Add to PATH"), then Route B |
| You cannot install anything | Talk to the instructor — see the note at the bottom |

---

## Route A: Docker on the VDI

Same as on your laptop. In the VS Code terminal:

```powershell
docker compose up -d --build
docker compose exec -T backend python -m app.seeds.seed_data
```

Open http://localhost:3030.

Most VDIs block this, because running Docker inside an already-virtual machine
needs nested virtualization and IT usually turns it off. If it fails, do not
fight it — Route B is the normal way to develop anyway.

---

## Route B: Run it directly (the usual VDI route)

### B1. A database

Pick one:

- **PostgreSQL installed on the VDI** — https://www.postgresql.org/download/windows/
  During setup, set a password for the `postgres` user and keep port `5432`.
  Afterwards open pgAdmin, right-click **Databases → Create → Database**, call
  it `acme_pm`.
  Your connection string:
  `postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/acme_pm`

- **A free cloud database** — sign up at https://neon.com, create a project,
  copy the connection string it gives you, and insert `+psycopg2` after
  `postgresql` so it reads
  `postgresql+psycopg2://user:pass@host/dbname?sslmode=require`

### B2. Tell the app where the database is

In VS Code, open the `backend` folder in the file tree. Copy `.env.example` to
a new file called exactly **`.env`** in the same folder, and put your
connection string in it:

```
DATABASE_URL=postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/acme_pm
JWT_SECRET=any-long-random-text-you-like
CORS_ORIGINS=http://localhost:3030
```

Doing it this way means you never have to retype the connection string again.

### B3. Install and start — the click-only way

VS Code can run all of this for you. Press `Ctrl + Shift + P`, type
**Run Task**, press Enter, and you will see this list:

```
1. Install backend dependencies
2. Load demo data
3. Install frontend dependencies
Run backend
Run frontend
Run everything
```

Run them in that order: **1**, then **2**, then **3**, then **Run everything**.

Tasks 1–3 finish and stop. "Run everything" keeps running — that is correct,
it means the servers are alive. Leave those terminal panels open.

### B4. Or do it by hand, if you prefer to see what's happening

Open two terminals in VS Code (`` Ctrl + ` ``, then click the **split** icon,
or the `+` to add a second one).

**Terminal 1 — backend**

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python -m app.seeds.seed_data
uvicorn app.main:app --reload
```

**Terminal 2 — frontend**

```powershell
cd frontend
npm install
npm run dev
```

Open http://localhost:3030 and sign in as `admin@acme.com` / `Admin@123`.

> If `.\.venv\Scripts\activate` is refused with an execution policy error, run
> this once, then try again:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

---

## Part 3: Working in VS Code day to day

- **Select the Python interpreter** so VS Code understands the backend code:
  `Ctrl + Shift + P` → **Python: Select Interpreter** → choose the one inside
  `backend/.venv`.
- **Install the recommended extensions.** VS Code will offer them when you open
  the folder — Python, Pylance and ESLint are the useful ones.
- **Both servers reload automatically.** Save a file in `backend/app/` and
  uvicorn restarts itself; save a file in `frontend/src/` and the browser
  updates on its own. You do not need to stop and restart anything.
- **Stop a server** with `Ctrl + C` in its terminal.
- **The API documentation** lives at http://localhost:8000/docs — every
  endpoint, clickable. Useful for showing the instructor the backend without
  going through the UI.

## Part 4: Committing your work

The instructor will likely want to see commit history, not one giant upload.

```powershell
git add .
git commit -m "Add budget variance column to the project list"
git push
```

`.gitignore` already keeps `node_modules`, `.venv` and `.env` out of the repo —
which matters, because `.env` holds your database password.

---

## If you cannot install anything on the VDI

Say so to the instructor early rather than on demo day. Ask specifically:

> Can you tell me which of these is already available on the VDI image, or can
> be requested: Python 3.11+, Node.js 18+, and a PostgreSQL instance I can
> connect to? The application is a standard React and FastAPI stack.

Most workshop VDIs are pre-loaded with exactly this, because the brief calls
for React, Python and PostgreSQL. It is worth asking before assuming.
