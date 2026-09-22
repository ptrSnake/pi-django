"""Tests for the user_update service (STILE-DJANGO.md §10.3)."""

from django.test import TestCase

from users.services import user_update
from users.tests.factories import UserFactory


class UserUpdateTests(TestCase):
    """Tests for the user_update service."""

    def test_user_update_changes_only_listed_fields(self) -> None:
        user = UserFactory(email="old@example.com", name="Old name")

        updated = user_update(user=user, data={"name": "New name"})

        self.assertEqual(updated.name, "New name")
        self.assertEqual(updated.email, "old@example.com")

    def test_user_update_returns_unchanged_instance(self) -> None:
        user = UserFactory(email="same@example.com")

        updated = user_update(user=user, data={})

        self.assertEqual(updated, user)
