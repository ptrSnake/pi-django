# __PROJECT_TITLE__

Django project scaffolded with the [pi-django](https://pi.dev/packages) extension, following the
conventions of the [Django Style Guide](https://github.com/HackSoftware/Django-Styleguide) (services/selectors domain
layer, UUID primary keys, `config/django` settings package, uv + ruff + pytest).

## Quickstart

```bash
uv sync              # install deps from uv.lock (env: .venv)
uv run python manage.py migrate
uv run python manage.py createsuperuser
uv run python manage.py runserver
```

## Development

```bash
uv run ruff check . && uv run ruff format --check .
uv run pytest
```

- Lint/format: ruff (Django Style Guide §2.2)
- Tests: pytest + pytest-django (`DJANGO_SETTINGS_MODULE=config.django.test`)
- Dev tools: django-extensions (`shell_plus`, `runserver_plus`, `show_urls`)

## Structure

```text
config/            settings package (§8): env.py, django/{base,local,test,production}.py
users/             custom User app (UUID PK, email login) with services/selectors/forms
templates/         Django templates (server-rendered variant)
```

## Notes

- Business logic lives in `users/services.py` / `users/selectors.py` (§4-§5).
- `BaseModel` (in `users/models.py`) provides the UUID primary key + timestamps (§3.1).
- Add a `core` app later if you need the `ApplicationError` hierarchy (§9.1).