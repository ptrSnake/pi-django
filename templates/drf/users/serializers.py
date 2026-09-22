"""Serializers for the users DRF API."""

from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from users.models import User
from users.services import user_create


class UserReadSerializer(serializers.ModelSerializer):
    """Read-only representation of a user."""

    class Meta:
        model = User
        fields = ("id", "email", "name", "is_active", "is_staff")


class RegisterSerializer(serializers.Serializer):
    """Registration serializer; creates the user through the service layer (§4)."""

    email = serializers.EmailField()
    name = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")
    password = serializers.CharField(write_only=True, validators=[validate_password])

    def validate_email(self, value: str) -> str:
        """Reject already-registered email addresses."""
        if User.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data: dict) -> User:
        """Create the user through the user_create service."""
        return user_create(**validated_data)
