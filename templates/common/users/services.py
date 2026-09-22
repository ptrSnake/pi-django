"""Business logic for users: services write data (STILE-DJANGO.md §4)."""

from django.db import transaction

from users.models import User


@transaction.atomic
def model_update(*, instance: User, fields: list[str], data: dict) -> tuple[User, bool]:
    """Update only the listed `fields` of `instance` with values from `data` (§12.1)."""
    has_updated = False

    for field in fields:
        if field in data:
            value = data[field]
            if getattr(instance, field) != value:
                setattr(instance, field, value)
                has_updated = True

    if has_updated:
        instance.full_clean()
        instance.save(update_fields=fields)

    return instance, has_updated


def user_create(*, email: str, name: str = "", password: str | None = None) -> User:
    """Create a new user with a hashed password, validating before saving (§4)."""
    email = email.strip().lower()
    user = User(email=email, name=name)
    user.set_password(password)
    user.full_clean()
    user.save()
    return user


def user_update(*, user: User, data: dict) -> User:
    """Update the editable fields of an existing user."""
    fields = ["email", "name"]

    user, _ = model_update(instance=user, fields=fields, data=data)

    return user
