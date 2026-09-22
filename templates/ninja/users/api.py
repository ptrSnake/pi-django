"""Ninja API for the users app (JWT auth via django-ninja-jwt)."""

from django.contrib.auth import authenticate
from django.http import HttpRequest
from ninja import NinjaAPI
from ninja.errors import HttpError
from ninja_jwt.authentication import JWTAuth
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import User
from users.schemas import LoginIn, RegisterIn, TokenOut, UserOut
from users.services import user_create

api = NinjaAPI(title="API", version="1.0.0")
api_auth = JWTAuth()


def _tokens_for_user(user: User) -> dict[str, str]:
    """Return access and refresh tokens for the given user."""
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


@api.post("/auth/register", response=TokenOut, auth=None)
def register(request: HttpRequest, payload: RegisterIn) -> dict[str, object]:
    """Register a new user and return JWT tokens."""
    if User.objects.filter(email=payload.email.lower()).exists():
        raise HttpError(409, "A user with this email already exists.")

    user = user_create(email=payload.email, name=payload.name, password=payload.password)

    return {**_tokens_for_user(user), "user": user}


@api.post("/auth/login", response=TokenOut, auth=None)
def login(request: HttpRequest, payload: LoginIn) -> dict[str, object]:
    """Authenticate with email and password and return JWT tokens."""
    user = authenticate(request, email=payload.email, password=payload.password)
    if user is None:
        raise HttpError(401, "Invalid email or password.")

    return {**_tokens_for_user(user), "user": user}


@api.get("/auth/me", response=UserOut, auth=api_auth)
def me(request: HttpRequest) -> User:
    """Return the currently authenticated user."""
    return request.auth
