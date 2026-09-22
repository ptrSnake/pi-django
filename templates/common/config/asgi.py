"""ASGI config for the __PROJECT_NAME__ project."""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.django.local")

application = get_asgi_application()
