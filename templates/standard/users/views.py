"""Views for the users app: thin bridges between HTTP, forms and services (§6)."""

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views import View

from users.forms import LoginForm, RegisterForm
from users.services import user_create


class RegisterView(View):
    """Register a new user and log them in (§6.7)."""

    template_name = "users/register.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        """Render the registration form."""
        form = RegisterForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request: HttpRequest) -> HttpResponse:
        """Validate the form, create the user through the service and log them in."""
        form = RegisterForm(data=request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form}, status=400)

        user = user_create(
            email=form.cleaned_data["email"],
            name=form.cleaned_data.get("name", ""),
            password=form.cleaned_data["password"],
        )
        login(request, user)
        messages.success(request, "Welcome!")
        return redirect("users:home")


class LoginView(View):
    """Log a user in with email and password."""

    template_name = "users/login.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        """Render the login form."""
        form = LoginForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request: HttpRequest) -> HttpResponse:
        """Authenticate the user and log them in."""
        form = LoginForm(data=request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form}, status=400)

        user = authenticate(
            request,
            email=form.cleaned_data["email"],
            password=form.cleaned_data["password"],
        )
        if user is None:
            messages.error(request, "Invalid email or password.")
            return render(request, self.template_name, {"form": form}, status=400)

        login(request, user)
        messages.success(request, "Welcome back!")
        return redirect("users:home")


class LogoutView(View):
    """Log the current user out (POST only)."""

    def post(self, request: HttpRequest) -> HttpResponse:
        """Terminate the session and redirect to the login page."""
        logout(request)
        return redirect("users:login")


class HomeView(View):
    """Landing page shown to any user."""

    template_name = "users/home.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        """Render the landing page."""
        return render(request, self.template_name, {})
