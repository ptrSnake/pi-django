"""Test settings (DJANGO_SETTINGS_MODULE=config.django.test, used by pytest)."""

from .base import *  # noqa: F403

# Faster password hashing in tests.
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]
