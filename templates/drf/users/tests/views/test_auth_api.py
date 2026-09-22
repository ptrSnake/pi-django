"""Tests for the DRF JWT auth endpoints (Django Styleguide §10.4)."""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import User
from users.tests.factories import UserFactory


class AuthApiTests(APITestCase):
    """Tests for the JWT auth endpoints."""

    def test_register_returns_tokens_and_creates_user(self) -> None:
        response = self.client.post(
            reverse("auth:register"),
            {"email": "someone@example.com", "name": "Someone", "password": "test-password-123"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertTrue(User.objects.filter(email="someone@example.com").exists())

    def test_register_rejects_duplicate_email(self) -> None:
        UserFactory(email="someone@example.com")

        response = self.client.post(
            reverse("auth:register"),
            {"email": "someone@example.com", "password": "test-password-123"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_me_requires_authentication(self) -> None:
        response = self.client.get(reverse("auth:me"))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_returns_authenticated_user(self) -> None:
        UserFactory(email="me@example.com", password="test-password-123")

        response = self.client.post(
            reverse("auth:token-obtain-pair"),
            {"email": "me@example.com", "password": "test-password-123"},
            format="json",
        )
        token = response.data["access"]

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.get(reverse("auth:me"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "me@example.com")
