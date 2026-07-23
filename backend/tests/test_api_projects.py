"""Integration tests for the project API: CRUD, validation and filtering."""

from tests.conftest import auth_headers

PAYLOAD = {
    "code": "PRJ-100",
    "name": "Integration Test Project",
    "description": "Created by the test suite",
    "department": "Engineering",
    "status": "active",
    "priority": 1,
    "start_date": "2026-01-01",
    "end_date": "2026-12-31",
    "planned_budget": 250000,
}


class TestProjectCrud:
    def test_create_returns_201_and_the_record(self, client, admin_user):
        headers = auth_headers(client, "admin@test.com", "Admin@123")

        response = client.post("/api/projects", json=PAYLOAD, headers=headers)

        assert response.status_code == 201
        body = response.json()
        assert body["code"] == "PRJ-100"
        assert body["id"] > 0
        # Calculated fields must be present even on a brand new project.
        assert "risk_level" in body
        assert "completion_pct" in body

    def test_read_back_after_create(self, client, admin_user):
        headers = auth_headers(client, "admin@test.com", "Admin@123")
        created = client.post("/api/projects", json=PAYLOAD, headers=headers).json()

        response = client.get(f"/api/projects/{created['id']}", headers=headers)

        assert response.status_code == 200
        assert response.json()["name"] == PAYLOAD["name"]

    def test_update_changes_only_what_was_sent(self, client, admin_user):
        headers = auth_headers(client, "admin@test.com", "Admin@123")
        created = client.post("/api/projects", json=PAYLOAD, headers=headers).json()

        response = client.patch(
            f"/api/projects/{created['id']}",
            json={"name": "Renamed Project"},
            headers=headers,
        )

        assert response.status_code == 200
        assert response.json()["name"] == "Renamed Project"
        # Untouched fields must survive a partial update.
        assert response.json()["department"] == "Engineering"

    def test_delete_returns_204_and_removes_it(self, client, admin_user):
        headers = auth_headers(client, "admin@test.com", "Admin@123")
        created = client.post("/api/projects", json=PAYLOAD, headers=headers).json()

        deleted = client.delete(f"/api/projects/{created['id']}", headers=headers)
        follow_up = client.get(f"/api/projects/{created['id']}", headers=headers)

        assert deleted.status_code == 204
        assert follow_up.status_code == 404


class TestProjectValidation:
    def test_missing_required_field_returns_422(self, client, admin_user):
        headers = auth_headers(client, "admin@test.com", "Admin@123")

        response = client.post(
            "/api/projects", json={"name": "No code or dates"}, headers=headers
        )

        assert response.status_code == 422

    def test_duplicate_code_returns_409(self, client, admin_user):
        headers = auth_headers(client, "admin@test.com", "Admin@123")
        client.post("/api/projects", json=PAYLOAD, headers=headers)

        response = client.post("/api/projects", json=PAYLOAD, headers=headers)

        assert response.status_code == 409

    def test_end_before_start_returns_400(self, client, admin_user):
        headers = auth_headers(client, "admin@test.com", "Admin@123")
        bad = {**PAYLOAD, "start_date": "2026-12-31", "end_date": "2026-01-01"}

        response = client.post("/api/projects", json=bad, headers=headers)

        assert response.status_code == 400

    def test_missing_project_returns_404(self, client, admin_user):
        headers = auth_headers(client, "admin@test.com", "Admin@123")

        response = client.get("/api/projects/9999", headers=headers)

        assert response.status_code == 404

    def test_invalid_status_value_is_rejected(self, client, admin_user):
        headers = auth_headers(client, "admin@test.com", "Admin@123")
        bad = {**PAYLOAD, "status": "not_a_real_status"}

        response = client.post("/api/projects", json=bad, headers=headers)

        assert response.status_code == 422


class TestProjectFiltering:
    def _seed(self, client, headers):
        client.post("/api/projects", json=PAYLOAD, headers=headers)
        client.post(
            "/api/projects",
            json={
                **PAYLOAD,
                "code": "PRJ-200",
                "name": "Finance Initiative",
                "department": "Finance",
                "status": "planning",
            },
            headers=headers,
        )

    def test_filter_by_status(self, client, admin_user):
        headers = auth_headers(client, "admin@test.com", "Admin@123")
        self._seed(client, headers)

        response = client.get("/api/projects?status=planning", headers=headers)

        assert response.status_code == 200
        assert all(p["status"] == "planning" for p in response.json())

    def test_filter_by_department(self, client, admin_user):
        headers = auth_headers(client, "admin@test.com", "Admin@123")
        self._seed(client, headers)

        response = client.get("/api/projects?department=Finance", headers=headers)

        assert len(response.json()) == 1
        assert response.json()[0]["department"] == "Finance"

    def test_search_matches_the_name(self, client, admin_user):
        headers = auth_headers(client, "admin@test.com", "Admin@123")
        self._seed(client, headers)

        response = client.get("/api/projects?search=Finance", headers=headers)

        assert len(response.json()) == 1

    def test_search_with_no_matches_returns_empty(self, client, admin_user):
        headers = auth_headers(client, "admin@test.com", "Admin@123")
        self._seed(client, headers)

        response = client.get("/api/projects?search=NothingMatchesThis", headers=headers)

        assert response.json() == []

    def test_departments_endpoint_lists_distinct_values(self, client, admin_user):
        headers = auth_headers(client, "admin@test.com", "Admin@123")
        self._seed(client, headers)

        response = client.get("/api/projects/departments", headers=headers)

        assert sorted(response.json()) == ["Engineering", "Finance"]


class TestSystemEndpoints:
    def test_health_check_needs_no_token(self, client):
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json()["status"] == "ok"
