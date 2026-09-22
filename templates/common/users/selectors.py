"""Reads for users: selectors read data (STILE-DJANGO.md §5)."""

from users.filters import UserFilter
from users.models import User


def user_list(*, fetched_by: User | None = None, filters: dict | None = None) -> list[User]:
    """List users; superusers are hidden for non-superusers, filtering via UserFilter."""
    filters = filters or {}

    qs = User.objects.all()

    if fetched_by is not None and not fetched_by.is_superuser:
        qs = qs.exclude(is_superuser=True)

    qs = UserFilter(filters, qs).qs

    return list(qs.order_by("email"))
