"""Models for the users app (STILE-DJANGO.md §3)."""

from __future__ import annotations

import uuid

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils import timezone


class BaseModel(models.Model):
    """Abstract base model: UUID primary key + timestamps (STILE-DJANGO.md §3.1)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    created_at = models.DateTimeField(db_index=True, default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UserManager(BaseUserManager):
    """Custom manager for User, using email as the unique identifier."""

    use_in_migrations = True

    def _create_user(self, *, email: str, password: str | None, **extra_fields: object) -> User:
        """Create and save a user with the given email and password."""
        if not email:
            raise ValueError("Users must have an email address")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(
        self, *, email: str, password: str | None = None, **extra_fields: object
    ) -> User:
        """Create a regular (non-staff, non-superuser) user."""
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email=email, password=password, **extra_fields)

    def create_superuser(
        self, *, email: str, password: str | None = None, **extra_fields: object
    ) -> User:
        """Create a superuser."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self._create_user(email=email, password=password, **extra_fields)


class User(BaseModel, AbstractBaseUser, PermissionsMixin):
    """Custom user model: email login, UUID primary key, no auto-increment id (§1.4)."""

    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255, blank=True, default="")

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"

    def __str__(self) -> str:
        """Return the string representation of the user."""
        return self.email

    @property
    def full_name(self) -> str:
        """Return the display name, falling back to the email."""
        return self.name.strip() or self.email
