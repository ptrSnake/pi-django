"""Tests for the user_create service (Django Styleguide §10.3)."""

from django.core.exceptions import ValidationError
from django.test import TestCase

from users.models import User
from users.services import user_create


class UserCreateTests(TestCase):
    """Tests for the user_create service."""

    def test_user_create_hashes_password(self) -> None:
        user = user_create(email="someone@example.com", password="test-password-123")

        self.assertFalse(user.password == "test-password-123")
        self.assertTrue(user.check_password("test-password-123"))

    def test_user_create_normalizes_email(self) -> None:
        user = user_create(email="Someone@Example.COM")

        self.assertEqual(user.email, "someone@example.com")

    def test_user_create_flags_defaults(self) -> None:
        user = user_create(email="someone@example.com")

        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_user_create_rejects_duplicate_email(self) -> None:
        user_create(email="someone@example.com")

        with self.assertRaises(ValidationError):
            user_create(email="someone@example.com")

    def test_create_superuser_via_manager(self) -> None:
        user = User.objects.create_superuser(email="admin@example.com", password="admin-password")

        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
