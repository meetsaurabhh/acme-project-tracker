# Running with your own PostgreSQL (no Docker)

Everything runs directly on the machine: PostgreSQL installed as a Windows
service, Python running the API, Node running the frontend. Three terminals,
no containers.

---

## Step 1 — Stop anything Docker is still running

Docker's PostgreSQL is holding port 5432, and its frontend is holding 3030.
Both must be free.

In the VS Code terminal, from the project folder:

```powershell
docker compose down
```

Check nothing is left:

```powershell
docker ps
```

An empty list (headers only) is what you want.

---

## Step 2 — Install PostgreSQL

1. Download the Windows installer from
   https://www.postgresql.org/download/windows/ — click "Download the
   installer", then pick **PostgreSQL 16** for Windows x86-64.
2. Run it. Accept the defaults for install location and components.
3. **When it asks for a password**, this is the password for the `postgres`
   superuser. Pick something you will remember and write it down — you need it
   in Step 4. There is no recovery if you forget it.
4. **Port**: leave it as `5432`.
5. **Locale**: leave as default.
6. At the end it offers to launch Stack Builder. Untick it. You don't need it.

### Check it installed

```powershell
Get-Service postgresql*
```

You should see a service with Status `Running`. If it says `Stopped`:

```powershell
Start-Service postgresql-x64-16
```

---

## Step 3 — Create the database

The installer gives you **pgAdmin 4**. Open it from the Start menu.

1. It asks for a master password the first time. This is pgAdmin's own
   password, separate from the postgres one. Set anything.
2. In the tree on the left: **Servers → PostgreSQL 16**. Click it. It asks for
   the password you set in Step 2.
3. Right-click **Databases → Create → Database…**
4. Name it exactly `acme_pm`. Click Save.

### Or do it from the terminal instead

If you prefer, and `psql` is on your PATH:

```powershell
psql -U postgres -c "CREATE DATABASE acme_pm;"
```

It prompts for the password. `CREATE DATABASE` means it worked.

> If `psql` isn't recognised, it's at
> `C:\Program Files\PostgreSQL\16\bin\psql.exe` — either use the full path or
> add that folder to your PATH.

---

## Step 4 — Tell the backend where the database is

In VS Code, open the `backend` folder in the file tree. Create a new file
called exactly **`.env`** (right-click the `backend` folder → New File).

Put this in it, replacing `YOUR_PASSWORD` with the password from Step 2:

```
DATABASE_URL=postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/acme_pm
JWT_SECRET=any-long-random-text-you-like
CORS_ORIGINS=http://localhost:3030
```

Save it.

The backend reads this file automatically when you start it from the `backend`
folder, so you never have to retype the connection string.

> **If your password contains `@`, `:`, `/`, `#` or `?`**, it will break the
> URL. Either change the password to letters and numbers only, or percent-encode
> it (`@` becomes `%40`, `#` becomes `%23`).

---

## Step 5 — Start the backend

In the VS Code terminal:

```powershell
cd backend
```

```powershell
python -m venv .venv
```

```powershell
.\.venv\Scripts\activate
```

Your prompt now starts with `(.venv)`. That means the virtual environment is
active and packages install into this project rather than system-wide.

```powershell
pip install -r requirements.txt
```

Takes a minute or two.

```powershell
python -m app.seeds.seed_data
```

This creates all the tables and loads the demo portfolio. You should see:

```
Seed complete.
  admin@acme.com   / Admin@123    (full access)
  manager@acme.com / Manager@123
  viewer@acme.com  / Viewer@123
```

```powershell
uvicorn app.main:app --reload
```

It prints `Uvicorn running on http://127.0.0.1:8000`. **Leave this terminal
running.** Closing it stops the API.

Check it: open http://localhost:8000/docs in a browser.

---

## Step 6 — Start the frontend

Open a **second** terminal in VS Code — click the `+` icon in the terminal
panel, or the split-pane icon. The first one must keep running.

```powershell
cd frontend
```

```powershell
npm install
```

```powershell
npm run dev
```

It prints `Local: http://localhost:3030/`.

Open that and sign in as `admin@acme.com` / `Admin@123`.

---

## Every time you come back to it

Two terminals, three commands:

**Terminal 1**
```powershell
cd backend
.\.venv\Scripts\activate
uvicorn app.main:app --reload
```

**Terminal 2**
```powershell
cd frontend
npm run dev
```

You don't rerun `pip install`, `npm install` or `python -m app.seeds.seed_data` — those
were one-time. PostgreSQL starts with Windows on its own, so there is nothing
to start there.

Stop either server with `Ctrl + C` in its terminal.

---

## The VS Code shortcut

If you'd rather not type: press `Ctrl + Shift + P`, type **Run Task**, Enter.
Pick **Run everything**. It starts both servers in their own panels.

The numbered tasks (1, 2, 3) are the one-time install steps and only need
running once.

---

## Useful database commands

**See your data** — in pgAdmin: Servers → PostgreSQL 16 → Databases → acme_pm →
Schemas → public → Tables. Right-click any table → **View/Edit Data → All
Rows**. Good for showing an assessor that the data is really in PostgreSQL.

**Reset to fresh demo data:**

```powershell
cd backend
.\.venv\Scripts\activate
python -m app.seeds.seed_data
```

**Wipe everything and start over:** drop the `acme_pm` database in pgAdmin,
create it again, then run the seed.

---

## When something breaks

| Message | What it means | Fix |
|---|---|---|
| `connection to server at "localhost" failed` | PostgreSQL isn't running | `Start-Service postgresql-x64-16` |
| `password authentication failed for user "postgres"` | Wrong password in `.env` | Check Step 2's password; watch for special characters |
| `database "acme_pm" does not exist` | Step 3 was skipped | Create it in pgAdmin |
| `.venv\Scripts\activate` "cannot be loaded" | PowerShell execution policy | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, then retry |
| `Port 5432 is already in use` | Docker's postgres still running | `docker compose down` |
| `Port 3030 is already in use` | Docker's frontend still running | `docker compose down` |
| Frontend loads but every request fails | Backend isn't running | Check Terminal 1; visit http://localhost:8000/docs |
| `ModuleNotFoundError` | venv not activated | Look for `(.venv)` in your prompt |

---

## What to say about this setup

The application code is identical whether the database is in Docker or
installed natively. The only thing that changes is one line — `DATABASE_URL` —
because SQLAlchemy sits between the code and the database, and nothing in
`app/` ever names a host.

That is worth pointing out. It is the same property that lets the same code run
against RDS in AWS without modification.
