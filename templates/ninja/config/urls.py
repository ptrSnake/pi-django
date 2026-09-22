"""Root URL configuration (Django Styleguide §7)."""

from django.contrib import admin
from django.urls import path

from users.api import api

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
]
