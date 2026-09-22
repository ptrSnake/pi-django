"""Factories for the users tests (Django Styleguide §10.5)."""

import factory
from django.contrib.auth import get_user_model

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    """Factory for the custom User model; uses the manager so passwords are hashed."""

    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    name = factory.Faker("name")
    password = "password123"

    @classmethod
    def _create(cls, model_class: type[User], *args: object, **kwargs: object) -> User:
        """Create the user through UserManager.create_user."""
        manager = cls._get_manager(model_class)
        return manager.create_user(*args, **kwargs)
