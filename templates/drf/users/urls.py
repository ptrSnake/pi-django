"""URLs for the users DRF API (STILE-DJANGO.md §7)."""

from django.urls import include, path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from users.auth_views import MeView, RegisterView

auth_patterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("token/", TokenObtainPairView.as_view(), name="token-obtain-pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("me/", MeView.as_view(), name="me"),
]

urlpatterns = [
    path("api/auth/", include((auth_patterns, "auth"))),
]
