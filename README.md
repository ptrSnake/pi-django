# pi-django

A [pi](https://pi.dev) extension that creates a **Django** project from scratch following the
conventions of the included [Django Style Guide](docs/django-styleguide.md)
(service layer, UUID primary keys, `config/django` settings package, uv + ruff + pytest).

- Uses **[uv](https://docs.astral.sh/uv/)** to initialize the project, dependencies, and environment.
- Asks (or accepts as parameters) the **framework**: `standard` (server-rendered),
  `drf` (Django REST Framework + JWT), or `ninja` (Django Ninja + JWT).
- Asks (or accepts as a parameter) the **Python version** (default: newest stable, 3.14).
- Generates the base structure with a ready-to-use **users** app: custom email + UUID model,
  manager, admin, services/selectors/filters, tests with factories, and auth flows.

## Installation

```bash
# from npm
pi install npm:pi-django

# from git (with a pinned tag/commit)
pi install git:github.com/<user>/pi-django@v1.0.0

# or via URL
pi install https://github.com/<user>/pi-django

# try without installing (current run only)
pi -e npm:pi-django
```

Remove with `pi remove npm:pi-django` (or `pi remove git:...`).

## Requirements

- [`uv`](https://docs.astral.sh/uv/) installed and on your `PATH`.
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
- `git` (only for git-based installation).

## Usage

### `django_scaffold` tool (from the model)

Ask in natural language, e.g.:

> Create a new Django project named `my-blog` using Django Ninja.

The tool accepts these parameters:

| Parameter | Required | Description |
|---|---|---|
| `project_name` | yes | Project name/slug. Use `.` to scaffold into the current directory. |
| `framework` | no | `standard` \| `drf` \| `ninja`. If omitted, the extension asks. |
| `python_version` | no | e.g. `3.14`. If omitted, the extension asks (default: newest). |
| `target_dir` | no | Parent directory (default: cwd). The project is created at `<target_dir>/<project_name>`. |

### `/django-scaffold` command

```
/django-scaffold <project-name> [standard|drf|ninja] [python-version]
```

Examples:

```
/django-scaffold my-blog standard
/django-scaffold api-service drf 3.13
/django-scaffold . ninja
```

## Local usage

To use the package locally before publishing (from this repository):

```bash
# 1. point pi at this repo (no copying, it adds the path to settings)
pi install /path/to/pi-django

# or, to avoid installing, just run a session with the extension loaded
pi -e /path/to/pi-django
```

Then, in a pi session:

- ask in natural language: "create a Django project called demo with DRF and Python 3.13"
  (if you do not specify framework/version, pi-django will ask you interactively), or
- use the command directly:
  ```
  /django-scaffold demo drf 3.13
  ```

You can watch the scaffolding happen step by step (uv init → uv add → migrations → check).
The project is created in `<cwd>/demo` and is ready to run.

## What gets generated

```text
<project>/
├── pyproject.toml            # uv: deps, [tool.ruff] (§2.2), [tool.pytest.ini_options]
├── uv.lock                   # always committed (§2.1)
├── .python-version
├── .env / .env.example       # django-environ; .env must not be committed (§8.3)
├── manage.py
├── config/
│   ├── env.py
│   ├── django/{base,local,test,production}.py   # settings (§8)
│   ├── urls.py, wsgi.py, asgi.py
└── users/                    # ready-to-use app
    ├── models.py             # BaseModel (UUID PK) + custom User (email login)
    ├── admin.py
    ├── services.py           # user_create, user_update, model_update (§4, §12.1)
    ├── selectors.py          # user_list (§5)
    ├── filters.py            # UserFilter (django-filter, §5.1)
    ├── migrations/           # initial migration already generated
    └── tests/                # models, services, selectors, views + factories (§10)
```

For the `standard` framework, explicit views (`django.views.View`), forms, and templates
(register / login / logout / home) are added. For `drf` and `ninja`, JWT endpoints are added
(`register`, `token`/`login`, `me`) with the authentication configuration.

The tool runs automatically:

1. `uv init` (bare project, chosen Python version);
2. `uv add` of the runtime dependencies for the framework;
3. `uv add --dev ruff pytest pytest-django factory-boy django-extensions`;
4. `uv run python manage.py makemigrations users`;
5. `uv run python manage.py check`.

## After scaffolding

```bash
cd <project>
uv run python manage.py migrate
uv run python manage.py createsuperuser
uv run python manage.py runserver

uv run ruff check . && uv run ruff format --check .
uv run pytest
```

- `standard`: http://localhost:8000/register
- `drf`: `POST /api/auth/register/`, `POST /api/auth/token/`, `GET /api/auth/me/`
- `ninja`: http://localhost:8000/api/docs

## Notes

- The tool never overwrites existing non-empty directories.
- If the chosen Python version is not installed, uv automatically downloads a managed interpreter.
- Django/DRF/Ninja versions are the current stable ones at scaffold time (latest on PyPI).

## Development

```bash
# structure
extensions/index.ts    # django_scaffold tool + /django-scaffold command
templates/common/      # files shared by all frameworks
templates/{standard,drf,ninja}/   # framework-specific files
templates/fragments/   # fragments for config/django/base.py
docs/                  # Django Style Guide + planning docs

# local harness (uv mocked, writes into a temp dir)
node --experimental-strip-types test/load-test.ts

# real end-to-end test
cd /tmp && pi -e /path/to/pi-django -p "Create a standard django project named demo"
```

## License

MIT — see [LICENSE](LICENSE).

The included [Django Style Guide](docs/django-styleguide.md) is an adaptation of the
[Django Styleguide by HackSoft](https://github.com/HackSoftware/Django-Styleguide)
(MIT, © 2019–2025 HackSoft); credits are listed at the end of that document.