"""Forms for the users app (Django Styleguide §6)."""

from typing import Any

from django import forms

from users.models import User


class RegisterForm(forms.Form):
    """Registration form: validates email uniqueness and password match."""

    email = forms.EmailField()
    name = forms.CharField(max_length=255, required=False)
    password = forms.CharField(widget=forms.PasswordInput)
    password_confirm = forms.CharField(widget=forms.PasswordInput)

    def clean(self) -> dict[str, Any]:
        """Validate password match and email uniqueness."""
        cleaned_data = super().clean()

        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError("The two passwords do not match.")

        email = cleaned_data.get("email")
        if email and User.objects.filter(email=email).exists():
            raise forms.ValidationError({"email": "A user with this email already exists."})

        return cleaned_data


class LoginForm(forms.Form):
    """Login form for email + password authentication."""

    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
