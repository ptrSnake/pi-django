"""Tests for the Ninja auth endpoints (Django Styleguide §10.4)."""

from django.test import TestCase

from users.models import User
from users.tests.factories import UserFactory


class AuthApiTests(TestCase):
    """Tests for the Ninja auth endpoints."""

    def test_register_returns_tokens_and_creates_user(self) -> None:
        response = self.client.post(
            "/api/auth/register",
            data={
                "email": "someone@example.com",
                "name": "Someone",
                "password": "test-password-123",
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("access", data)
        self.assertIn("refresh", data)
        self.assertTrue(User.objects.filter(email="someone@example.com").exists())

    def test_register_rejects_duplicate_email(self) -> None:
        UserFactory(email="someone@example.com")

        response = self.client.post(
            "/api/auth/register",
            data={"email": "someone@example.com", "password": "test-password-123"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 409)

    def test_me_requires_authentication(self) -> None:
        response = self.client.get("/api/auth/me")

        self.assertEqual(response.status_code, 401)

    def test_me_returns_authenticated_user(self) -> None:
        UserFactory(email="me@example.com", password="test-password-123")

        login = self.client.post(
            "/api/auth/login",
            data={"email": "me@example.com", "password": "test-password-123"},
            content_type="application/json",
        )
        token = login.json()["access"]

        response = self.client.get("/api/auth/me", HTTP_AUTHORIZATION=f"Bearer {token}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["email"], "me@example.com")
