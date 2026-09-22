"""Tests for the user_list selector (STILE-DJANGO.md §10)."""

from django.test import TestCase

from users.selectors import user_list
from users.tests.factories import UserFactory


class UserListTests(TestCase):
    """Tests for the user_list selector."""

    def test_user_list_returns_all_users_ordered_by_email(self) -> None:
        first = UserFactory(email="first@example.com")
        second = UserFactory(email="second@example.com")

        users = user_list()

        self.assertEqual(list(users), [first, second])

    def test_user_list_filters_by_email(self) -> None:
        UserFactory(email="first@example.com")
        wanted = UserFactory(email="second@example.com")

        users = user_list(filters={"email": "second"})

        self.assertEqual(list(users), [wanted])

    def test_user_list_hides_superusers_from_regular_users(self) -> None:
        admin = UserFactory(email="admin@example.com", is_staff=True, is_superuser=True)
        regular = UserFactory(email="regular@example.com")

        users = user_list(fetched_by=regular)

        self.assertEqual(list(users), [regular])
        self.assertNotIn(admin, users)
