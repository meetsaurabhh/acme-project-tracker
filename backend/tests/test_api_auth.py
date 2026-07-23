"""Integration tests for authentication and role-based access control.

These exercise the full HTTP stack: route, dependency, service, database.
"""

from tests.conftest import auth_headers


class TestAuthentication:
    def test_valid_credentials_return_a_token(self, client, admin_user):
        response = client.post(
            "/api/auth/login",
            data={"username": "admin@test.com", "password": "Admin@123"},
        )

        assert response.status_code == 200
        assert "access_token" in response.json()

    def test_wrong_password_is_rejected(self, client, admin_user):
        response = client.post(
            "/api/auth/login",
            data={"username": "admin@test.com", "password": "WrongPassword"},
        )

        assert response.status_code == 401

    def test_unknown_email_gives_the_same_error(self, client, admin_user):
        """The message must not reveal which emails are registered."""
        unknown = client.post(
            "/api/auth/login",
            data={"username": "nobody@test.com", "password": "Admin@123"},
        )
        wrong_password = client.post(
            "/api/auth/login",
            data={"username": "admin@test.com", "password": "WrongPassword"},
        )

        assert unknown.status_code == wrong_password.status_code == 401
        assert unknown.json()["detail"] == wrong_password.json()["detail"]

    def test_deactivated_account_cannot_sign_in(self, client, db_session, admin_user):
        admin_user.is_active = False
        db_session.commit()

        response = client.post(
            "/api/auth/login",
            data={"username": "admin@test.com", "password": "Admin@123"},
        )

        assert response.status_code == 403

    def test_email_is_case_insensitive(self, client, admin_user):
        response = client.post(
            "/api/auth/login",
            data={"username": "ADMIN@TEST.COM", "password": "Admin@123"},
        )

        assert response.status_code == 200

    def test_profile_endpoint_returns_the_signed_in_user(self, client, admin_user):
        headers = auth_headers(client, "admin@test.com", "Admin@123")

        response = client.get("/api/auth/me", headers=headers)

        assert response.status_code == 200
        assert response.json()["email"] == "admin@test.com"
        # The password hash must never leave the server.
        assert "hashed_password" not in response.json()


class TestTokenEnforcement:
    def test_request_without_a_token_is_rejected(self, client):
        response = client.get("/api/projects")

        assert response.status_code == 401

    def test_request_with_a_bad_token_is_rejected(self, client):
        response = client.get(
            "/api/projects", headers={"Authorization": "Bearer not-a-real-token"}
        )

        assert response.status_code == 401


class TestRoleBasedAccessControl:
    """The rules that actually protect the data, tested at the HTTP boundary."""

    PROJECT_PAYLOAD = {
        "code": "PRJ-NEW",
        "name": "New Project",
        "start_date": "2026-01-01",
        "end_date": "2026-12-31",
        "planned_budget": 10000,
    }

    def test_viewer_can_read(self, client, viewer_user):
        headers = auth_headers(client, "viewer@test.com", "Viewer@123")

        response = client.get("/api/projects", headers=headers)

        assert response.status_code == 200

    def test_viewer_cannot_create(self, client, viewer_user):
        headers = auth_headers(client, "viewer@test.com", "Viewer@123")

        response = client.post(
            "/api/projects", json=self.PROJECT_PAYLOAD, headers=headers
        )

        assert response.status_code == 403
        assert "viewer" in response.json()["detail"]

    def test_manager_can_create(self, client, manager_user):
        headers = auth_headers(client, "manager@test.com", "Manager@123")

        response = client.post(
            "/api/projects", json=self.PROJECT_PAYLOAD, headers=headers
        )

        assert response.status_code == 201

    def test_manager_cannot_manage_accounts(self, client, manager_user):
        headers = auth_headers(client, "manager@test.com", "Manager@123")

        response = client.post(
            "/api/users",
            json={
                "email": "new@test.com",
                "full_name": "New User",
                "role": "viewer",
                "password": "Password123",
            },
            headers=headers,
        )

        assert response.status_code == 403

    def test_admin_can_manage_accounts(self, client, admin_user):
        headers = auth_headers(client, "admin@test.com", "Admin@123")

        response = client.post(
            "/api/users",
            json={
                "email": "new@test.com",
                "full_name": "New User",
                "role": "viewer",
                "password": "Password123",
            },
            headers=headers,
        )

        assert response.status_code == 201

    def test_admin_cannot_delete_their_own_account(self, client, admin_user):
        """Guards against locking every administrator out of the platform."""
        headers = auth_headers(client, "admin@test.com", "Admin@123")

        response = client.delete(f"/api/users/{admin_user.id}", headers=headers)

        assert response.status_code == 400
