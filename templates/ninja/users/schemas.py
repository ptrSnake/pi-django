"""Pydantic schemas for the users Ninja API."""

from ninja import ModelSchema, Schema

from users.models import User


class UserOut(ModelSchema):
    """User representation returned by the API."""

    class Meta:
        model = User
        fields = ["id", "email", "name", "is_active", "is_staff"]


class RegisterIn(Schema):
    """Registration payload."""

    email: str
    name: str = ""
    password: str


class LoginIn(Schema):
    """Login payload."""

    email: str
    password: str


class TokenOut(Schema):
    """JWT tokens plus the authenticated user."""

    access: str
    refresh: str
    user: UserOut
