"""Tests for the User model (STILE-DJANGO.md §3.6)."""

from django.test import TestCase

from users.tests.factories import UserFactory


class UserModelTests(TestCase):
    """Tests for the User model."""

    def test_str_returns_email(self) -> None:
        user = UserFactory(email="someone@example.com")

        self.assertEqual(str(user), "someone@example.com")

    def test_full_name_falls_back_to_email(self) -> None:
        user = UserFactory(email="someone@example.com", name="")

        self.assertEqual(user.full_name, "someone@example.com")

    def test_create_user_uses_email_username_field(self) -> None:
        user = UserFactory(email="someone@example.com")

        self.assertEqual(user.get_username(), "someone@example.com")
