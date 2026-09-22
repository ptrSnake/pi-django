# pi-django

Estensione [pi](https://pi.dev) che crea da zero un progetto **Django** seguendo le
convenzioni di [`STILE-DJANGO.md`](https://github.com/HackSoftware/Django-Styleguide)
(service layer, UUID come primary key, settings in `config/django`, uv + ruff + pytest).

- Usa **[uv](https://docs.astral.sh/uv/)** per inizializzare il progetto, le dipendenze e l'environment.
- Chiede (o accetta come parametri) il **framework**: `standard` (server-rendered),
  `drf` (Django REST Framework + JWT) o `ninja` (Django Ninja + JWT).
- Chiede (o accetta come parametro) la **versione di Python** (default: la più recente, 3.14).
- Genera la struttura base con l'app **users** già pronta: modello custom email + UUID,
  manager, admin, services/selectors/filters, test con factory, e flussi di auth.

## Installazione

```bash
# da npm
pi install npm:pi-django

# da git (con tag/commit fissato)
pi install git:github.com/<utente>/pi-django@v1.0.0

# oppure via URL
pi install https://github.com/<utente>/pi-django

# prova senza installare (sessione corrente)
pi -e npm:pi-django
```

Rimuovi con `pi remove npm:pi-django` (o `pi remove git:...`).

## Requisiti

- [`uv`](https://docs.astral.sh/uv/) installato e nel `PATH`.
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
- `git` (solo per l'installazione da git).

## Uso

### Tool `django_scaffold` (dal modello)

Chiedi in linguaggio naturale, ad esempio:

> Crea un nuovo progetto Django chiamato `my-blog` con Django Ninja.

Il tool accetta questi parametri:

| Parametro | Obbligatorio | Descrizione |
|---|---|---|
| `project_name` | sì | Nome/slug del progetto. Usa `.` per generare nella directory corrente. |
| `framework` | no | `standard` \| `drf` \| `ninja`. Se assente, l'estensione lo chiede. |
| `python_version` | no | Es. `3.14`. Se assente, l'estensione lo chiede (default: più recente). |
| `target_dir` | no | Directory padre (default: cwd). Il progetto viene creato in `<target_dir>/<project_name>`. |

### Comando `/django-scaffold`

```
/django-scaffold <project-name> [standard|drf|ninja] [python-version]
```

Esempi:

```
/django-scaffold my-blog standard
/django-scaffold api-service drf 3.13
/django-scaffold . ninja
```

## Cosa viene generato

```text
<project>/
├── pyproject.toml            # uv: deps, [tool.ruff] (§2.2), [tool.pytest.ini_options]
├── uv.lock                   # sempre committato (§2.1)
├── .python-version
├── .env / .env.example       # django-environ; .env non va committato (§8.3)
├── manage.py
├── config/
│   ├── env.py
│   ├── django/{base,local,test,production}.py   # settings (§8)
│   ├── urls.py, wsgi.py, asgi.py
└── users/                    # app pronta all'uso
    ├── models.py             # BaseModel (PK UUID) + User custom (email login)
    ├── admin.py
    ├── services.py           # user_create, user_update, model_update (§4, §12.1)
    ├── selectors.py          # user_list (§5)
    ├── filters.py            # UserFilter (django-filter, §5.1)
    ├── migrations/           # migrazione iniziale già generata
    └── tests/                # models, services, selectors, views + factories (§10)
```

Per il framework `standard` vengono aggiunti view esplicite (`django.views.View`), form e
template (register / login / logout / home). Per `drf` e `ninja` vengono aggiunti endpoint
JWT (`register`, `token`/`login`, `me`) e la configurazione di autenticazione.

Il tool esegue automaticamente:

1. `uv init` (progetto bare, versione Python scelta);
2. `uv add` delle dipendenze runtime del framework;
3. `uv add --dev ruff pytest pytest-django factory-boy django-extensions`;
4. `uv run python manage.py makemigrations users`;
5. `uv run python manage.py check`.

## Dopo la generazione

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

## Note

- Il tool non sovrascrive directory esistenti non vuote.
- Se la versione Python scelta non è installata, uv scarica automaticamente un
  interprete gestito.
- Le versioni di Django/DRF/Ninja sono quelle correnti al momento dello scaffold
  (ultima stabile disponibile su PyPI).

## Sviluppo

```bash
# struttura
extensions/index.ts    # tool django_scaffold + comando /django-scaffold
templates/common/      # file comuni a tutti i framework
templates/{standard,drf,ninja}/   # file specifici
templates/fragments/   # frammenti per config/django/base.py

# harness locale (uv mockato, scrive in una dir temporanea)
node --experimental-strip-types test/load-test.ts

# prova end-to-end reale
cd /tmp && pi -e /percorso/di/pi-django -p "Crea un progetto django standard chiamato demo"
```

## Licenza

MIT
