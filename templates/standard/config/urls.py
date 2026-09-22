"""Root URL configuration (STILE-DJANGO.md §7)."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("users.urls")),
]
