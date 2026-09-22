# Piano: pi-package `pi-django` — scaffold di progetti Django

## Contesto

Creare un **pi-package** distribuito via npm e git che fornisce un **tool** (e un comando)
per generare da zero un progetto Django conforme a `STILE-DJANGO.md` (nel cwd del repo):

- usa **uv** per inizializzare il progetto e gestire dipendenze/env;
- chiede all'utente quale framework usare: **Django standard (server-rendered)**,
  **Django REST Framework**, **Django Ninja**;
- chiede/accetta come parametro la **versione Python** (default: la più recente, 3.14+);
- crea la struttura base del progetto;
- include l'app **users** già pronta all'uso: modello, manager, admin, services/selectors/
  filters, tests/factory **e flussi di auth** (register/login/logout per standard;
  register/login/token refresh/me con **JWT** per DRF e Ninja).

**Fattibilità — verificata sulla documentazione di pi (0.87.0):**
- Le estensioni girano con pieni permessi di sistema e possono eseguire comandi
  (`child_process`/`node:fs`): possono lanciare `uv init`, `uv add`, `make migrations`, ecc.
- `pi.registerTool()` espone un tool al modello con parametri typebox (`StringEnum` per gli
  enum, compatibile con Google) e `execute(toolCallId, params, signal, onUpdate, ctx)` dove
  `ctx.cwd` è la directory di lavoro corrente.
- L'estensione può **chiedere all'utente** durante l'esecuzione: `ctx.ui.select / confirm /
  input / editor` (guardia `ctx.hasUI`; in modalità headless si cade su default).
- File bundle relativi al sorgente dell'estensione: pattern `dirname(fileURLToPath(import.meta.url))`
  già usato dagli esempi ufficiali (`examples/extensions/doom-overlay/wad-finder.ts`,
  `dynamic-resources/index.ts`) → si possono includere i template di scaffolding come asset.
- Il manifest `pi` in `package.json` dichiara `extensions`, `skills`, `prompts`, `themes`;
  keyword `pi-package` per la gallery. Thrid-party runtime deps in `dependencies`;
  `@earendil-works/pi-coding-agent` e `typebox` in `peerDependencies` con `"*"` (non bundle).
- Toolchain presente nella macchina: uv 0.11.32, Python 3.12.3, node 24, npm 11.
  `uv init --bare --name X` confermato.

## Approccio

**Struttura del pacchetto pi (`pi-django`):**

```
pi-django/
├── package.json              # name "pi-django", keywords ["pi-package"], manifest pi
├── README.md                 # installazione (npm/git), utilizzo del tool
├── extensions/
│   └── index.ts              # registra tool "django_scaffold" (+ comando /django-scaffold)
└── templates/                # asset dello scaffold (bundled, letti via import.meta.url)
    ├── empty/                # file comuni ai 3 framework (config/, manage.py, .env, ecc.)
    ├── users/                # app users nei 3 varianti (standard/drf/ninja)
    └── pyproject-patch/      # frammenti [tool.ruff], [tool.pytest.ini_options]
```

**Flusso del tool `django_scaffold`:**

1. `project_name` (slug) e `target_dir` (default: `ctx.cwd/<project_name>`; `"."` = cwd);
   verifica che la cartella non esista già o sia vuota.
2. `framework`: `StringEnum(["standard","drf","ninja"])`. Se assente → se `ctx.hasUI`,
   `ctx.ui.select("Framework Django", [...])`; altrimenti default `"standard"`.
3. `python_version`: stringa (default `"3.14"`); se assente e `ctx.hasUI` →
   `ctx.ui.select("Versione Python", [3.14, 3.13, 3.12, …])` (uv scarica managed Python
   se la versione non è presente sul sistema). `requires-python` nel pyproject e
   `target-version` di ruff derivati da questa scelta.
4. `uv init --bare --name <name> --python <ver> <dir>` → poi scrive sopra i file del
   progetto (template bundled) e aggiorna `pyproject.toml` (name, requires-python,
   `[tool.ruff]`, pytest).
5. `uv add django django-environ django-filter` + deps per framework
   (drf: `djangorestframework` + `djangorestframework-simplejwt`; ninja: `django-ninja`
   + `django-ninja-jwt`). `uv add --dev ruff pytest pytest-django factory-boy`.
6. Scrive i file del progetto (vedi "Cosa viene generato").
7. `uv run python manage.py makemigrations users` → genera la migrazione dell'app users.
8. Risposta finale con istruzioni (`uv run python manage.py migrate`, `runserver`, test).

**Cosa viene generato** (conforme a STILE-DJANGO.md):

- `manage.py`; `pyproject.toml` con `requires-python`, `[tool.ruff]` (§2.2:
  `target-version`, `line-length = 100`, select E/W/F/I/UP/B/SIM/ANN/D,
  `known-first-party = ["config", "<progetto>"]`), `[tool.pytest.ini_options]` con
  `DJANGO_SETTINGS_MODULE=config.django.test` (§14).
- `config/` (§8): `config/__init__.py`, `config/env.py` (django-environ),
  `config/django/{__init__,base,local,production,test}.py`,
  `config/settings/__init__.py` (pronto per integrazioni: celery/sentry/cors/sessions),
  `config/urls.py`, `wsgi.py`, `asgi.py`.
  `INSTALLED_APPS` include l'app users; `AUTH_USER_MODEL="users.User"`;
  `DEFAULT_AUTO_FIELD="django.db.models.UUIDField"` (uuid default anche fuori da BaseModel, §3.1).
- `.gitignore` (.venv, .env, __pycache__, ecc.), `.env.example`, `.env`, `.python-version`,
  `README.md` del progetto.
- **App `users`** "pronta per essere utilizzata", nei tre varianti:
  - comune: `models.py` (BaseUser: email unica + name + flag, pk UUID via `BaseModel`,
    manager custom con `create_user`/`create_superuser`), `admin.py`, `apps.py`?
    (config), `tests/` con struttura §10 (`tests/services/`, `tests/selectors/`,
    `tests/factories.py` con factory_boy), `services.py` (`user_create`, `user_update` con
    `model_update` §12.1), `selectors.py` (`user_list` con FilterSet §5), `filters.py`.
  - **standard** (server-rendered): `forms.py` (registrazione/login), views esplicite
    (`django.views.View`, §6: register/login/logout), `urls.py` (`*_patterns` §7),
    template `users/` base (login/register) estendibile (§6.3 naming
    `<app>/<modello>_<azione>.html`).
  - **drf** (JWT): `serializers.py` (Register, UserRead), `api.py` con endpoints
    `/api/auth/register`, `/api/auth/token` (TokenObtainPair), `/api/auth/refresh`,
    `/api/auth/me` (JWT `IsAuthenticated`), config `SIMPLE_JWT` in `base.py`;
    `rest_framework`+`rest_framework_simplejwt` in INSTALLED_APPS.
  - **ninja** (JWT): `api.py` con router `/api/auth/register`, `/api/auth/login`
    (restituisce access/refresh via semplice chiamata a simplejwt),
    `/api/auth/me` protetto con JWT (django-ninja-jwt), `schemas.py`; doc in `/api/docs`.
- Eventuali piccole differenze per framework in `base.py` (INSTALLED_APPS e SIMPLE_JWT).

## File da creare (pacchetto pi)

- `package.json` — `name: "pi-django"`, `version`, `keywords: ["pi-package"]`,
  `peerDependencies`: `@earendil-works/pi-coding-agent` `"*"`, `typebox` `"*"`,
  manifest `pi: { extensions: ["./extensions"] }`; `files` per il tarball npm
  (extensions/, templates/, README.md).
- `extensions/index.ts` — tool `django_scaffold` + command `/django-scaffold`
  (stessa logica; utile anche senza modello).
- `templates/…` — tutti i file sorgente generati (con placeholder `{{project_name}}` ecc.).
- `README.md` — installazione (`pi install npm:pi-django` / `pi install git:…`),
  utilizzo, verifica.
- (opzionale) `EXTENSIONS.md` con note di sviluppo interno.

## Riuso

- API pi: `pi.registerTool` (+ `StringEnum` da `@earendil-works/pi-ai` per enum Google),
  `ctx.ui.select/confirm`, `ctx.cwd`, `ctx.hasUI`, `withFileMutationQueue` (non necessario
  qui ma da tenere presente se il tool mai modifica file esistenti).
- Pattern asset bundled: `dirname(fileURLToPath(import.meta.url))` — es.
  `examples/extensions/doom-overlay/wad-finder.ts`.
- Esempi tool: `examples/extensions/hello.ts` (minimal), `dynamic-tools.ts`.
- Guida Django: `STILE-DJANGO.md` nel cwd (riferimenti § elencati sopra).

## Passi

- [x] Scelte di design confermate: app users completa con auth (C); JWT per API;
  output in sottocartella (default) con `"."` per il cwd; Python default più recente
  con scelta utente; nome npm pubblico non scoped `pi-django`.
- [x] Scaffoldare il pacchetto: `package.json`, `extensions/index.ts`, `templates/`
- [x] Implementare la generazione: render dei template ({{placeholders}} + per-framework)
- [x] Implementare i comandi uv (init bare, add, dev add) con `child_process` e log progressivo
- [x] App users per i 3 framework + config/ + pyproject patch
- [x] Test locale del tool con `pi -e .` in una directory scratch
- [x] Verifica end-to-end dei 3 scaffold (check, migrate, tests, ruff)
- [x] Pubblicazione: `npm publish` (pubblico) + repo git con tag `v1.0.0`
- [x] README con istruzioni di installazione da npm e git

## Verifica

1. `pi -e .` nella root del pacchetto → verificare che `django_scaffold` sia attivo.
2. In una cartella temporanea, far eseguire al tool lo scaffold per i 3 framework:
   `pi -e <percorso-pacchetto> -c "Crea un progetto django standard chiamato demo"` o
   tramite invocazione del tool nella sessione.
3. Per ogni progetto generato (standard, drf, ninja; Python 3.14 e 3.12):
   - `uv run python manage.py check` → ok;
   - `uv run python manage.py migrate` e `django-admin showmigrations users` → migrazione presente;
   - `uv run pytest` → i test della app users passano;
   - `uv run ruff check . && uv run ruff format --check .` → puliti;
   - `uv run python manage.py runserver` → pagine/flussi auth raggiungibili
     (login/register per standard; `/api/auth/token` etc. per drf; `/api/docs`
     e `/api/auth/me` per ninja);
4. Installazione come pacchetto reale: `pi install git:github.com/<user>/pi-django@v1.0.0`
   e `pi install npm:pi-django`, poi `pi list` e test del tool.
5. Gallery: keyword `pi-package` (opzionale `pi.video`/`pi.image`).