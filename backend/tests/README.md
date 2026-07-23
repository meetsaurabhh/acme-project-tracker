# Test suite

## Running the tests

```bash
cd backend
source .venv/bin/activate
pip install -r requirements-dev.txt
pytest
```

## What is covered

| File | Type | What it tests |
|---|---|---|
| `test_project_service.py` | Unit | The six risk rules, progress and budget maths, date validation |
| `test_allocation_service.py` | Unit | Capacity limits, over-allocation, part-time hours |
| `test_deliverable_service.py` | Unit | Dependency chain ordering, circular references, overdue logic |
| `test_api_auth.py` | Integration | Sign-in, token enforcement, all three roles |
| `test_api_projects.py` | Integration | Full CRUD, validation errors, search and filters |

Unit tests call services directly with no HTTP layer. Integration tests go
through the real routes, dependencies and database.

## How it works

Every test runs against a fresh in-memory SQLite database, created and thrown
away per test. No PostgreSQL server is needed and tests cannot interfere with
each other or leave state behind.

`conftest.py` overrides the `get_db` dependency so the application uses the
test database instead of the real one.

## Coverage report

```bash
pytest --cov=app --cov-report=html
```

Then open `htmlcov/index.html`.

## Known gaps

Named deliberately rather than hidden:

- **Frontend tests are not written.** Jest and React Testing Library would
  cover the components; Cypress would cover end-to-end journeys.
- **Budget and user services** have integration coverage through the API but
  no dedicated unit tests.
- **Load testing** has not been done. Artillery against `/api/analytics/summary`
  would be the place to start, since it is the heaviest endpoint.
- **SQLite is not PostgreSQL.** The tests would not catch a PostgreSQL-specific
  SQL problem. Running the same suite against a real PostgreSQL in CI would
  close that gap.
