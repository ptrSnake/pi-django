"""URLs for the users app: one URL per view (STILE-DJANGO.md §7)."""

from django.urls import include, path

from users.views import HomeView, LoginView, LogoutView, RegisterView

user_patterns = [
    path("", HomeView.as_view(), name="home"),
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
]

urlpatterns = [
    path("", include((user_patterns, "users"))),
]
