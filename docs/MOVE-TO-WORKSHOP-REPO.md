# Moving into the workshop repo

Your project already has the shape the workshop expects. This is a move, not a
rewrite.

---

## What changes and why

| Thing | Before | After | Why |
|---|---|---|---|
| Location | `~/acme-project-tracker` | `~/coding-workshop-participant/backend/python-service` | Their Terraform looks there |
| Entry point | `lambda_handler.py` | `function.py` with `handler()` | Their template requires this name |
| Database config | `DATABASE_URL` | `POSTGRES_HOST`, `POSTGRES_USER`, etc. | Their platform injects these |
| Frontend port | 3030 | 3000 | Their architecture diagram |
| Backend port | 8000 | 3001 | Their architecture diagram |
| Tests | none | 66 tests | Testing is 20% of your score |

Nothing in the business logic changes. Not one service, model or route.

---

## Step 1 — Fork their repo

You cannot push to `citi/coding-workshop-participant`. Fork it first.

1. Go to https://github.com/Citi/coding-workshop-participant
2. Click **Fork**, top right
3. It becomes `meetsaurabhh/coding-workshop-participant`

Then point your local clone at your fork:

```bash
cd ~/coding-workshop-participant
git remote set-url origin https://github.com/meetsaurabhh/coding-workshop-participant.git
git remote -v
```

Both lines should now show your username.

> **If your clone has local changes from the setup scripts**, stash them first:
> `git stash`

---

## Step 2 — Create your service from their template

This is the command their guide specifies:

```bash
cd ~/coding-workshop-participant
cp -R backend/_examples/python-service backend/python-service
```

Now replace the hello-world contents with yours:

```bash
rm backend/python-service/function.py
rm backend/python-service/requirements.txt
```

Keep `postgres_service.py` and `mongo_service.py` for now — read them later to
see how they connect, then delete them once you are confident.

---

## Step 3 — Copy your application in

```bash
cp -R ~/acme-project-tracker/backend/app backend/python-service/
cp ~/acme-project-tracker/backend/function.py backend/python-service/
cp ~/acme-project-tracker/backend/requirements.txt backend/python-service/
cp ~/acme-project-tracker/backend/requirements-dev.txt backend/python-service/
cp ~/acme-project-tracker/backend/pytest.ini backend/python-service/
cp -R ~/acme-project-tracker/backend/tests backend/python-service/
```

Check what landed:

```bash
ls backend/python-service
```

You want: `app`, `tests`, `function.py`, `requirements.txt`,
`requirements-dev.txt`, `pytest.ini`.

---

## Step 4 — Copy the frontend in

Look at what their frontend folder already contains first:

```bash
ls frontend
```

If it holds an example app you are replacing:

```bash
cp -R ~/acme-project-tracker/frontend/src frontend/
cp ~/acme-project-tracker/frontend/index.html frontend/
cp ~/acme-project-tracker/frontend/package.json frontend/
cp ~/acme-project-tracker/frontend/vite.config.js frontend/
```

> If their frontend folder has its own structure or build config, **stop and
> ask an organiser** before overwriting. Their deployment script may expect
> specific files.

---

## Step 5 — Copy the documentation

Your docs are evidence for the Experience competency, which is scored.

```bash
mkdir -p docs/submission
cp ~/acme-project-tracker/docs/PROJECT-WALKTHROUGH.md docs/submission/
cp ~/acme-project-tracker/docs/BACKEND-ARCHITECTURE.md docs/submission/
cp ~/acme-project-tracker/docs/BUSINESS-QUESTIONS.md docs/submission/
```

---

## Step 6 — Run the tests

```bash
cd backend/python-service
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pytest
```

You should see 66 tests pass and a coverage table.

**This is the single most valuable thing you can show an assessor.** Testing is
one of five equally weighted technical competencies, and most participants
submit nothing for it.

To produce a coverage report you can point at:

```bash
pytest --cov=app --cov-report=html
```

Then open `htmlcov/index.html` in the VDI browser.

---

## Step 7 — Start their development environment

Their script wires everything to the right ports and injects the database
variables automatically:

```bash
cd ~/coding-workshop-participant
./bin/start-dev.sh
```

Then check your service is answering:

```bash
curl http://localhost:3001/api/python-service/health
```

> The exact path depends on how their API Gateway is configured. If that
> returns nothing, try `curl http://localhost:3001/health` and check the logs:
> `AWS_ENDPOINT_URL="http://localhost:4566" aws logs tail /aws/lambda/coding-workshop-python-service --follow`

---

## Step 8 — Point the frontend at the new API

Create `frontend/.env`:

```bash
cd ~/coding-workshop-participant/frontend
echo "VITE_API_URL=http://localhost:3001/api/python-service" > .env
```

Adjust the path once you have confirmed the real one in step 7.

---

## Step 9 — Commit and push

```bash
cd ~/coding-workshop-participant
git add -A
git commit -m "Add ACME project tracker: layered FastAPI service, React frontend, 66 tests"
git push
```

---

## Step 10 — Deploy

```bash
./bin/deploy-backend.sh
```

Their script handles the packaging and the Terraform. Watch the output for the
API base URL, then rebuild the frontend against it.

---

## How the environment variables now work

`app/core/config.py` was rewritten to read what their platform injects:

```python
POSTGRES_HOST, POSTGRES_PORT, POSTGRES_NAME, POSTGRES_USER, POSTGRES_PASS
```

It assembles the connection string from those, and when `IS_LOCAL` is `false`
it appends `sslmode=require` for Aurora — exactly as their guide requires.

A `DATABASE_URL` still overrides everything if one is set, so standalone
development on your own machine keeps working unchanged.

---

## What to raise with an organiser

Three things worth confirming rather than guessing:

1. **Is `python-service` the right service name?** It determines your API path.
2. **Should the frontend replace their `frontend/` folder, or sit inside it?**
3. **Does their deploy script expect a particular frontend build output path?**

Five minutes of asking beats an hour of moving files twice.

---

## Scoring, and where you stand

From `docs/full-stack.md`, five technical competencies are averaged:

| Competency | Where you stand |
|---|---|
| **Implementation** | Strong. Full CRUD, both layers integrated, runs locally. Cloud deploy is the remaining piece. |
| **Design** | Strong. Responsive via React Responsive, consistent Material UI, clean API contracts. |
| **Code** | Strong. Organised by domain across five layers, error handling throughout, no copy-paste. |
| **Testing** | Was the gap. 66 tests now cover the business logic and API contracts, with known gaps documented. |
| **Experience** | Strong. Documented setup, architecture written up, trade-offs stated. |

The documented known gaps in `tests/README.md` matter more than they look.
Their own criterion is *"test artifacts (commands, results, and known gaps) are
documented clearly"* — naming what you did not test scores better than
pretending you covered everything.
