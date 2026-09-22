# Guida allo stile Django

> **Documento di riferimento per lo sviluppo di progetti Django server-rendered.**
> La guida è riutilizzabile per qualunque progetto Django: non contiene riferimenti a un dominio specifico.
> È ispirata alla [Django Styleguide](https://github.com/HackSoftware/Django-Styleguide) di HackSoft,
> adattata però a un progetto che usa **template Django** (class-based views + form) e non un'API (DRF).
>
> Status: **v1.0** – documento di riferimento per il progetto corrente e per i futuri.

---

## 1. Che cos'è e come si usa

- È **pragmatica**: tutto ciò che è descritto qui è stato provato in produzione.
- È **opinata**: è *il nostro* modo di costruire applicazioni Django.
- **Non è l'unico modo**: esistono altri approcci validi per strutturare un progetto Django.

Quando si usa la guida esistono tre strade generali:

1. Seguire alla lettera tutto ciò che è scritto qui.
2. **Scegliere ciò che funziona per il proprio contesto (consigliato).**
3. Non seguire nulla di ciò che è scritto qui.

Il consiglio è il punto 2: leggi la guida, decidi cosa funziona per il tuo caso e adatta.

### 1.1 Principio chiave

La logica di business deve vivere in:

- **Services** – funzioni che si occupano principalmente di *scrivere* dati nel database.
- **Selectors** – funzioni che si occupano principalmente di *leggere* dati dal database.
- **Proprietà dei modelli** (con alcune eccezioni).
- **Metodo `clean` dei modelli** per validazioni aggiuntive (con alcune eccezioni).

La logica di business **non** deve vivere in:

- Views.
- Form.
- Template tag.
- Metodo `save` dei modelli.
- Manager o queryset custom.
- Signals.

### 1.2 Perché non mettere la logica nei modelli manager/queryset?

I manager e queryset custom sono strumenti potenti e vanno usati per esporre interfacce migliori sui modelli.
Ma non vanno usati come contenitore di tutta la logica di business perché:

- La logica di business ha un proprio dominio, non sempre mappato uno-a-uno sul modello dati.
- La logica spesso attraversa più modelli: dove mettiamo una logica che tocca i modelli A, B, C e D?
- Possono esserci chiamate a sistemi terzi: non le vogliamo dentro un manager.

L'idea è far vivere il dominio **separato** dal modello dati e dal layer di interfaccia (views/form/template).
Combinando queryset/manager custom con l'idea di dominio separato si arriva a ciò che chiamiamo **service layer**.
I servizi possono essere funzioni, classi, moduli: qualunque cosa abbia senso nel caso specifico.

### 1.3 Perché non mettere la logica nei signals?

Da tutte le opzioni disponibili, questa è forse quella che porta più rapidamente a una cattiva situazione:

- I signals sono ottimi per connettere cose che *non devono sapere l'una dell'altra*.
- Sono ottimi per gestire l'invalidazione della cache fuori dalla logica di business.
- Se iniziamo a usarli per cose strettamente connesse rendiamo la connessione **implicita** e più difficile da tracciare.

Consiglio: usare i signals solo per casi d'uso molto particolari, non per strutturare il dominio.

### 1.4 Convenzioni generali

Regole trasversali applicate a **tutto** il progetto.

**Lingua del codice – solo inglese.**

- Tutti i nomi – variabili, funzioni, classi, metodi, modelli, tabelle, campi, costanti – sono **in inglese**.
- Le docstring e i commenti sono **in inglese**.
- I messaggi di errore, i `verbose_name`/`verbose_name_plural` dei modelli e i testi tecnici sono **in inglese**.
- Questo documento guida resta in italiano, ma ogni frammento di codice riportato al suo interno è **in inglese**.
- La lingua dell'utente finale (UI) è indipendente: il testo mostrato nei template può essere italiano,
  ma identificatori, commenti e messaggi interni no.

Esempio (corretto):

```python
def order_cancel(*, order: Order) -> Order:  # ok
    ...
```

Esempio (errato):

```python
def cancella_ordine(*, ordine: Ordine) -> Ordine:  # errato
    ...
```

**Identificativi – UUID come chiave primaria.**

- Ogni modello ha una **chiave primaria UUID** e **nessun `id` intero auto-incrementale**.
- Il campo PK si chiama `id` ed è un `UUIDField(primary_key=True, default=uuid.uuid4, editable=False)`.
- Tutte le ForeignKey puntano alla chiave UUID del modello referenziato.
- I parametri che ricevono un identificativo (es. `user_id`, `order_id`) sono di tipo `uuid.UUID`, non `int`.
- Ciò vale per tutti i modelli, inclusi i modelli utente e quelli di dominio.

---

## 2. Tooling: uv e ruff

> Tutti i progetti nuovi iniziano con **uv** per la gestione di dipendenze ed environment e con **ruff**
> come unico strumento di linting **e** formattazione.

### 2.1 uv

[uv](https://docs.astral.sh/uv/) è il gestore di progetti/dipendenze Python usato per default.

Regole d'uso:

- Inizializzare il progetto con `uv init` e aggiungere Django con `uv add django`.
- Annotare la versione di Python richiesta in `[project].requires-python` del `pyproject.toml`
  e nel file `.python-version` (creato da `uv`).
- Il file `uv.lock` garantisce la riproducibilità degli ambienti ed è **sempre** committato.
- Tutti i comandi si eseguono con `uv run`:

```bash
uv run python manage.py runserver
uv run python manage.py migrate
uv run ruff check .
uv run ruff format .
uv run pytest
```

- Per le dipendenze di sviluppo (ruff, pytest, factory-boy, ecc.) usare il gruppo dedicato:

```bash
uv add --dev ruff pytest factory-boy
```

- Non installare pacchetti "alla cieca" nell'ambiente globale: tutto passa da `pyproject.toml`.

### 2.2 ruff

[ruff](https://docs.astral.sh/ruff/) è l'unico strumento per linting, formattazione e ordinamento degli import.

Regole d'uso:

- **`ruff check`** per il lint.
- **`ruff format`** per la formattazione (stile Black).
- Configurazione in `[tool.ruff]` del `pyproject.toml`; esempio minimale:

```toml
[tool.ruff]
target-version = "py314"
line-length = 100

[tool.ruff.lint]
select = [
    "E",    # pycodestyle
    "W",    # pycodestyle (warning)
    "F",    # pyflakes
    "I",    # isort
    "UP",   # pyupgrade
    "B",    # bugbear
    "SIM",  # simplify
    "ANN",  # annotations
    "D",    # pydocstyle (opzionale)
]

[tool.ruff.lint.isort]
known-first-party = ["config", "<nome_progetto>"]
```

- Prima di ogni commit: `uv run ruff check . && uv run ruff format --check .`.
- **Import sorting**: gli import vanno ordinati con la regola `I` (isort): prima stdlib, poi terze parti,
  poi Django, poi i moduli locali del progetto. Non ordinare mai a mano.
- **Type annotations**: services e selectors usano *keyword-only arguments* e sono annotati
  (regole `ANN`). L'annotazione è obbligatoria anche se non si usa mypy.
- L'uso di mypy è **opzionale** e dipende dal progetto (vedi §14).

---

## 3. Models

I modelli devono occuparsi del modello dati e non molto altro.

### 3.1 Base model

È buona pratica definire un `BaseModel` da ereditare.
Oltre alla chiave primaria **UUID** (obbligatoria per §1.4), campi come `created_at` e `updated_at`
sono candidati perfetti:

```python
import uuid

from django.db import models
from django.utils import timezone


class BaseModel(models.Model):
    # Chiave primaria UUID: nessun id intero auto-incrementale (§1.4).
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    created_at = models.DateTimeField(db_index=True, default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
```

Poi ogni modello eredita `BaseModel`:

```python
class SomeModel(BaseModel):
    pass
```

Nota: poiché `BaseModel` definisce già la chiave primaria UUID, impostare
`DEFAULT_AUTO_FIELD = "django.db.models.UUIDField"` in `base.py` garantisce che anche i modelli
che non ereditano da `BaseModel` usino UUID come default.

### 3.2 Validazione – clean e full_clean

Esempio:

```python
class Course(BaseModel):
    name = models.CharField(unique=True, max_length=255)

    start_date = models.DateField()
    end_date = models.DateField()

    def clean(self):
        if self.start_date >= self.end_date:
            raise ValidationError("La data di fine non può precedere la data di inizio")
```

Definiamo `clean` per garantire dati corretti nel database.
Affinché `clean` venga chiamato, qualcuno deve invocare `full_clean` sull'istanza prima del `save`.
Il consiglio è farlo **nel service**, subito prima del `save`:

```python
def course_create(*, name: str, start_date: date, end_date: date) -> Course:
    obj = Course(name=name, start_date=start_date, end_date=end_date)

    obj.full_clean()
    obj.save()

    return obj
```

Regole generali su quando validare in `clean`:

- Quando la validazione riguarda più campi **non relazionali** del modello.
- Quando la validazione è sufficientemente semplice.

La validazione va spostata nel service layer quando:

- La logica di validazione è più complessa.
- Sono necessarie relazioni trasversali o fetch di dati aggiuntivi.

È accettabile avere validazione sia in `clean` sia nel service, ma tendiamo a spostare le cose nel service.

### 3.3 Validazione – constraints

Se una validazione può essere espressa con i constraint di Django, va preferita quella via:
meno codice da scrivere e mantenere, e il database protegge i dati anche se inseriti da un altro punto.

```python
from django.db import models
from django.db.models import F, Q


class Course(BaseModel):
    name = models.CharField(unique=True, max_length=255)

    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        constraints = [
            models.CheckConstraint(
                name="start_date_before_end_date",
                check=Q(start_date__lt=F("end_date")),
            )
        ]
```

Nota: dal **Django 4.1** chiamare `full_clean` verifica anche i constraint del modello,
quindi nel service otterrai una `ValidationError` pulita e non una `IntegrityError`.
Se invece si passa da `Model.objects.create(...)` il downside resta (si riceve una `IntegrityError`).

Documentazione utile:

- https://docs.djangoproject.com/en/stable/ref/models/constraints/
- https://www.pythonmorsels.com/ (articoli di Adam Johnson sui CheckConstraint)

### 3.4 Proprietà

Le proprietà sono un ottimo modo per accedere rapidamente a un valore derivato dell'istanza:

```python
from django.utils import timezone


class Course(BaseModel):
    name = models.CharField(unique=True, max_length=255)

    start_date = models.DateField()
    end_date = models.DateField()

    @property
    def has_started(self) -> bool:
        now = timezone.now()
        return self.start_date <= now.date()

    @property
    def has_finished(self) -> bool:
        now = timezone.now()
        return self.end_date <= now.date()
```

Regole generali per aggiungere proprietà al modello:

- Serve un valore derivato semplice, basato su campi **non relazionali**: aggiungi una `@property`.
- Il calcolo del valore derivato è sufficientemente semplice.

La proprietà deve diventare qualcos'altro (service, selector, utility) quando:

- Serve attraversare più relazioni o fare fetch di dati aggiuntivi.
- Il calcolo è più complesso.

Regole volutamente vaghe: il contesto conta, usa il buon senso.

### 3.5 Metodi

I metodi costruiscono sulle proprietà quando serve un argomento:

```python
def is_within(self, x: date) -> bool:
    return self.start_date <= x <= self.end_date
```

`is_within` non può essere una proprietà perché richiede un argomento → è un metodo.

Un altro uso tipico dei metodi: impostare attributi in cui l'assegnazione di uno richiede sempre
l'assegnazione derivata di un altro:

```python
from django.conf import settings
from django.utils import timezone
from django.utils.crypto import get_random_string


class Token(BaseModel):
    secret = models.CharField(max_length=255, unique=True)
    expiry = models.DateTimeField(blank=True, null=True)

    def set_new_secret(self):
        now = timezone.now()

        self.secret = get_random_string(255)
        self.expiry = now + settings.TOKEN_EXPIRY_TIMEDELTA

        return self
```

Regole generali:

- Valore derivato semplice che richiede argomenti, basato su campi non relazionali → metodo.
- Impostare un attributo richiede sempre valori derivati su altri attributi → metodo.
- Serve attraversare relazioni/fetch dati o il calcolo è complesso → service/selector/utility.

### 3.6 Testing dei modelli

I modelli vanno testati solo se hanno qualcosa in più (validazione, proprietà, metodi):

```python
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from project.some_app.models import Course


class CourseTests(TestCase):
    def test_course_end_date_cannot_be_before_start_date(self):
        start_date = timezone.now()
        end_date = timezone.now() - timedelta(days=1)

        course = Course(start_date=start_date, end_date=end_date)

        with self.assertRaises(ValidationError):
            course.full_clean()
```

Note:

- Si verifica che venga sollevata una `ValidationError` chiamando `full_clean`.
- **Non si tocca il database**: in molti casi non serve, e questo velocizza i test.

---

## 4. Services

I services sono il luogo in cui vive la logica di business.
Il service layer parla il linguaggio del dominio, può accedere al database e ad altre risorse
e può interagire con altre parti del sistema.

Un service può essere:

- Una semplice funzione.
- Una classe.
- Un intero modulo.
- Qualunque cosa abbia senso nel caso specifico.

Nella maggior parte dei casi un service è una semplice funzione che:

- Vive nel modulo `<app>/services.py`.
- Prende **solo keyword-argument**, a meno che non richieda zero o un argomento.
- È annotata con i tipi (anche se non usi mypy al momento).
- Interagisce con database, risorse e altre parti del sistema.
- Fa logica di business: dalla creazione semplice di un modello a problemi trasversali complessi,
  fino alla chiamata di servizi esterni e task.

### 4.1 Esempio – service a funzione

```python
def user_create(*, email: str, name: str) -> User:
    user = User(email=email)
    user.full_clean()
    user.save()

    profile_create(user=user, name=name)
    confirmation_email_send(user=user)

    return user
```

Come si vede, questo service chiama altri due service – `profile_create` e `confirmation_email_send`.
Tutto ciò che riguarda la creazione dell'utente è in un unico punto e può essere tracciato.

### 4.2 Esempio – service a classe

Possiamo avere service "a classe": un modo elegante per incapsulare più comportamenti sotto un namespace.

```python
from django.db import transaction
from django.utils import timezone


class FileUploadService:
    """
    Esempio di service class che incapsula create & update sotto un namespace.
    La classe serve per:
    1. Il namespace.
    2. Il riuso di `_infer_file_name_and_type`.
    """

    def __init__(self, *, user: User, file_obj):
        self.user = user
        self.file_obj = file_obj

    def _infer_file_name_and_type(
        self, file_name: str = "", file_type: str = ""
    ) -> tuple[str, str]:
        file_name = file_name or self.file_obj.name
        if not file_type:
            import mimetypes

            guessed, _ = mimetypes.guess_type(file_name)
            file_type = guessed or ""
        return file_name, file_type

    @transaction.atomic
    def create(self, file_name: str = "", file_type: str = "") -> File:
        file_name, file_type = self._infer_file_name_and_type(file_name, file_type)

        obj = File(
            file=self.file_obj,
            original_file_name=file_name,
            file_name=file_generate_name(file_name),
            file_type=file_type,
            uploaded_by=self.user,
            upload_finished_at=timezone.now(),
        )
        obj.full_clean()
        obj.save()
        return obj
```

I service a classe sono indicati anche per i **flussi** (flow): cose che attraversano più step.

### 4.3 Convenzione di naming

Il pattern è **`<entità>_<azione>`**, ad esempio `user_create`, `course_update`, `order_cancel`.
Può sembrare strano all'inizio, ma ha vantaggi concreti:

- **Namespacing**: è facile individuare tutti i service che iniziano con `user_` e ha senso
  raggrupparli in un modulo `users.py`.
- **Greppability**: per vedere tutte le azioni su un'entità basta cercare `grep "user_"`.

### 4.4 Moduli

Se l'app è semplice, tutti i service vivono in `services.py`.
Quando il file cresce, lo si divide in una cartella con sottomoduli per sotto-dominio:

```text
services/
├── __init__.py
├── jwt.py
└── oauth.py
```

Si può fare l'import-export in `services/__init__.py` per continuare a importare da
`project.authentication.services`, oppure creare cartelle-modulo (`jwt/__init__.py`) e mettere lì il codice.
La struttura è a propria discrezione: quando senti che è il momento di ristrutturare, fallo.

---

## 5. Selectors

Nella maggior parte dei progetti distinguiamo tra "scrivere dati" e "leggere dati":

- I **services** si occupano della scrittura.
- Gli **selectors** si occupano della lettura.

Gli selectors possono essere visti come un *sotto-layer* dei services, specializzato nel fetch.
Se questa idea non risuona, si possono usare i services per entrambe le operazioni.

Un selector segue le stesse regole di un service (keyword-only, annotato, ecc.).

Esempio nel modulo `<app>/selectors.py`:

```python
def user_list(*, fetched_by: User) -> Iterable[User]:
    visible_ids = user_get_visible_for(user=fetched_by)
    return User.objects.filter(id__in=visible_ids)
```

Si possono restituire queryset, liste o qualunque cosa abbia senso nel caso specifico.
Il **filtro** (ricerca, parametri) è responsabilità del selector.

### 5.1 Filtri con django-filter

Per gestire la ricerca/filtraggio delle liste usiamo **django-filter**.

- Ogni app ha un modulo **`filters.py`** con le classi `FilterSet` dedicate ai suoi modelli.
- La classe di filtro definisce i campi filtrabili e la relativa logica (lookup esatti,
  icontains, choice, range, ecc.).
- Il selector riceve i parametri di filtro (dict o `request.GET`), applica il `FilterSet`
  al queryset e restituisce il risultato.

Esempio di `users/filters.py`:

```python
import django_filters

from users.models import BaseUser


class BaseUserFilter(django_filters.FilterSet):
    email = django_filters.CharFilter(lookup_expr="icontains")
    name = django_filters.CharFilter(lookup_expr="icontains")
    is_active = django_filters.BooleanFilter()
    is_staff = django_filters.BooleanFilter()

    class Meta:
        model = BaseUser
        fields = []
```

Esempio di selector che usa il filtro:

```python
from users.filters import BaseUserFilter


def user_list(*, fetched_by: BaseUser, filters: dict | None = None) -> list[BaseUser]:
    filters = filters or {}

    qs = BaseUser.objects.all()

    if not fetched_by.is_superuser:
        qs = qs.exclude(is_superuser=True)

    qs = BaseUserFilter(filters, qs).qs

    return list(qs.order_by("email"))
```

Regole:

- Il `FilterSet` espone **solo** i campi filtrabili, mai l'intero queryset.
- La responsabilità del filtro resta del selector: il `FilterSet` è un mezzo, non un fine.
- Per le viste di lista, la vista passa `request.GET` come `filters` (vedi §6.4).

### 5.2 Come creare una list query

Ricetta completa per costruire una lista filtrata, ordinata e paginata,
dal `FilterSet` fino al template.

#### 5.2.1 Tipi di filtro disponibili

`django-filter` espone un `Filter` per tipo di campo; il `lookup_expr` accetta
gli stessi lookup di Django (`exact`, `icontains`, `in`, `gte`, `lte`, `range`, ...).

| Filter | Uso tipico |
|---|---|
| `CharFilter` | Ricerca testuale: `CharFilter(lookup_expr="icontains")` |
| `BooleanFilter` | Flag booleani (es. `is_active`) |
| `NumberFilter` | Valori numerici esatti |
| `DateFilter` / `DateTimeFilter` | Date e datetime |
| `ChoiceFilter` | Campo con `choices` |
| `ModelChoiceFilter` | FK singola (select a tendina) |
| `ModelMultipleChoiceFilter` | FK multipla |
| `BaseInFilter` | Lookup `in` (es. `NumberFilter` + `BaseInFilter`) |
| `RangeFilter` | Lookup `range` (es. intervalli di date) |
| `OrderingFilter` | Ordinamento dal client |

```python
import django_filters
from django.forms import DateInput

from users.models import BaseUser


class BaseUserFilter(django_filters.FilterSet):
    email = django_filters.CharFilter(lookup_expr="icontains")
    name = django_filters.CharFilter(lookup_expr="icontains")
    is_active = django_filters.BooleanFilter()
    joined_after = django_filters.DateTimeFilter(field_name="date_joined", lookup_expr="gte")
    ordering = django_filters.OrderingFilter(fields=("email", "name", "-date_joined"))
```

#### 5.2.2 Convenzioni e best practice

- Un modulo **`filters.py`** per app, una classe **`<Model>Filter`** per modello.
- `Meta.fields = []` e campi **dichiarati esplicitamente**: il `FilterSet` espone
  solo ciò che si dichiara, mai l'intero queryset.
- Un `Filter` per campo, con `field_name` e `lookup_expr` espliciti
  (es. `joined_after` su `date_joined` con `gte`).
- La **responsabilità del filtro resta nel selector**: il `FilterSet` è un mezzo,
  non un fine; la logica di autorizzazione (es. escludere i superuser) sta nel selector.
- Guardia sempre presente: `filters = filters or {}`.
- **Ordinamento di default nel selector** (`order_by`), non nel `FilterSet`.
- **Paginazione nel selector**, che restituisce la `Page` di Django (vedi §6.4).
- La vista passa `request.GET` come `filters` e legge `page` dalla querystring.

#### 5.2.3 Ricetta end-to-end (con paginazione)

1. **`users/filters.py`** – definire i campi filtrabili:

```python
import django_filters

from users.models import BaseUser


class BaseUserFilter(django_filters.FilterSet):
    email = django_filters.CharFilter(lookup_expr="icontains")
    name = django_filters.CharFilter(lookup_expr="icontains")
    is_active = django_filters.BooleanFilter()
    ordering = django_filters.OrderingFilter(
        fields=(("email", "email"), ("name", "name"), ("-date_joined", "newest"))
    )

    class Meta:
        model = BaseUser
        fields = []
```

2. **`users/selectors.py`** – il selector applica filtro, ordinamento e paginazione:

```python
from django.core.paginator import Paginator

from users.filters import BaseUserFilter
from users.models import BaseUser


def user_list(*, fetched_by: BaseUser, filters: dict | None = None) -> Page:
    filters = filters or {}

    qs = BaseUser.objects.all()

    if not fetched_by.is_superuser:
        qs = qs.exclude(is_superuser=True)

    qs = BaseUserFilter(filters, qs).qs.order_by("email")

    paginator = Paginator(qs, per_page=25)
    return paginator.get_page(filters.get("page"))
```

3. **`users/views.py`** – la vista fa da ponte: selector + context:

```python
from django.shortcuts import render
from django.views import View

from users.selectors import user_list


class UserListView(View):
    template_name = "users/user_list.html"

    def get(self, request):
        page = user_list(fetched_by=request.user, filters=request.GET)

        return render(request, self.template_name, {"page": page})
```

4. **`users/urls.py`** – una rotta per view (vedi §7):

```python
from django.urls import path

from users.views import UserListView


user_patterns = [
    path("", UserListView.as_view(), name="list"),
]

urlpatterns = [
    path("users/", include((user_patterns, "users"))),
]
```

5. **`users/templates/users/user_list.html`** – solo presentazione: la pagina
   riceve `page` con la querystring di filtro già attiva, quindi i link di
   paginazione devono preservarla (es. `?email=x&page=2`):

```html
<form method="get">
  <input type="text" name="email" placeholder="Email">
  <input type="text" name="name" placeholder="Nome">
  <button type="submit">Cerca</button>
</form>

<ul>
  {% for user in page.object_list %}
    <li>{{ user.email }} – {{ user.name }}</li>
  {% empty %}
    <li>Nessun utente trovato.</li>
  {% endfor %}
</ul>

{% if page.has_other_pages %}
  <nav>
    {% if page.has_previous %}
      <a href="?{{ request.GET.urlencode }}&page={{ page.previous_page_number }}">Precedente</a>
    {% endif %}
    <span>Pagina {{ page.number }} di {{ page.paginator.num_pages }}</span>
    {% if page.has_next %}
      <a href="?{{ request.GET.urlencode }}&page={{ page.next_page_number }}">Successiva</a>
    {% endif %}
  </nav>
{% endif %}
```

Regole della ricetta:

- Il `FilterSet` si occupa **solo** del filtro; ordinamento e paginazione sono del selector.
- Il selector restituisce una `Page`; la vista la passa al template senza ulteriore logica.
- Il template non fa query né logica di dominio: solo loop e link di paginazione.

---

## 6. Views e Template

> Questa sezione sostituisce la sezione "APIs & Serializers" della styleguide originale,
> perché i progetti di riferimento renderizzano **template Django** e non espongono API.
> Non si usa DRF: niente serializer, niente `APIView`.

### 6.1 Principi

Le views sono **l'interfaccia** verso la logica di dominio. Regole generali:

- **Una view per operazione** (per il CRUD su un modello: list, detail, create, update, delete).
- Eredita dalla più semplice delle view: `django.views.View`.
- Evita le classi *generic* astratte (`ListView`, `CreateView`, ...): tendono a gestire le cose
  tramite form/queryset in modo implicito, e noi vogliamo farlo esplicitamente tramite services/selectors.
- **Niente business logic nella view.**
- Nella view si può fare il *fetch* dell'oggetto o la preparazione dei dati, ma la logica va nei service.

La view è un guscio sottile che fa da ponte tra la richiesta HTTP, la logica di dominio e il template.

### 6.2 Input e output

- **Input**: la validazione dei dati in ingresso è compito di un **Form** (`django.forms.Form` o `ModelForm`)
  dedicato. Il form valida e i dati puliti vengono passati al service.
- **Output**: non esistono serializer. La view passa al template i dati restituiti dal selector
  (oggetti, queryset, valori calcolati) nel *context* di `render`.

Schema ricorrente per ogni operazione:

1. View riceve la richiesta.
2. (opzionale) Form dedicato valida l'input.
3. View chiama un **selector** (lettura) o un **service** (scrittura).
4. View rende un **template** con i dati nel context; in caso di errore re-ndere il form con gli errori.

### 6.3 Convenzione di naming

- Views: **`<Entità><Azione>View`** → `CourseList`, `CourseDetail`, `CourseCreate`, `CourseUpdate`.
- Form: **`<Entità><Azione>Form`** → `CourseCreateForm`, `CourseUpdateForm`.
- Template: **`<app>/<modello>_<azione>.html`** → `courses/course_list.html`, `courses/course_create.html`.

### 6.4 List (con filtro e paginazione)

La view chiama un selector che applica filtro e paginazione e passa i risultati al template.

```python
# views.py
from django.views import View
from django.shortcuts import render

from project.courses.selectors import course_list


class CourseListView(View):
    template_name = "courses/course_list.html"

    def get(self, request):
        courses = course_list(filters=request.GET)

        return render(request, self.template_name, {"courses": courses})
```

```python
# selectors.py
import django_filters

from project.courses.models import Course


class CourseFilter(django_filters.FilterSet):
    class Meta:
        model = Course
        fields = ("name", "is_active")


def course_list(*, filters=None) -> list[Course]:
    filters = filters or {}

    qs = Course.objects.all()
    qs = CourseFilter(filters, qs).qs

    return list(qs)
```

> Il punto chiave: la **responsabilità del filtro è del selector**.
> I `FilterSet` vivono nel modulo `filters.py` dell'app e sono consumati dai selector
> (vedi §5.1).
> Per la paginazione vale lo stesso principio: se serve, si pagina dentro il selector
> (ad esempio con `django.core.paginator.Paginator`).

Esempio di view con paginazione dentro la logica:

```python
from django.core.paginator import Paginator
from django.views import View
from django.shortcuts import render


class CourseListView(View):
    template_name = "courses/course_list.html"

    def get(self, request):
        courses = course_list(filters=request.GET)

        paginator = Paginator(courses, per_page=25)
        page = paginator.get_page(request.GET.get("page"))

        return render(request, self.template_name, {"page": page})
```

### 6.5 Detail

```python
from django.views import View
from django.shortcuts import render

from project.courses.selectors import course_get


class CourseDetailView(View):
    template_name = "courses/course_detail.html"

    def get(self, request, course_id):
        course = course_get(course_id=course_id)

        return render(request, self.template_name, {"course": course})
```

### 6.6 Fetch degli oggetti

Quando una view riceve un id, dove si recupera l'oggetto? Opzioni:

- Recuperarlo nella view con una utility `get_object` e passarlo a service/selector.
- Passare l'id a service/selector e fare il fetch lì.

La scelta dipende dal contesto; l'importante è la **coerenza**. Pattern tipico:

```python
from django.shortcuts import get_object_or_404

from project.courses.models import Course


def course_get(*, course_id: int) -> Course:
    return get_object_or_404(Course, id=course_id)
```

Il `get_object_or_404` solleva `Http404`, che Django trasforma nella pagina "Non trovato".

### 6.7 Create (con form + service)

```python
# forms.py
from django import forms

from project.courses.models import Course


class CourseCreateForm(forms.Form):
    name = forms.CharField(max_length=255)
    start_date = forms.DateField()
    end_date = forms.DateField()
```

```python
# views.py
from django.views import View
from django.shortcuts import render, redirect

from project.courses.forms import CourseCreateForm
from project.courses.services import course_create


class CourseCreateView(View):
    template_name = "courses/course_create.html"

    def get(self, request):
        form = CourseCreateForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = CourseCreateForm(data=request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form}, status=400)

        course_create(**form.cleaned_data)

        return redirect("courses:list")
```

### 6.8 Update

Stesso schema del create, con il service di update. Il form può avere campi parziali:

```python
class CourseUpdateForm(forms.Form):
    name = forms.CharField(max_length=255, required=False)
    start_date = forms.DateField(required=False)
    end_date = forms.DateField(required=False)
```

La view recupera l'oggetto, valida il form e chiama il service:

```python
class CourseUpdateView(View):
    template_name = "courses/course_update.html"

    def get(self, request, course_id):
        course = course_get(course_id=course_id)
        form = CourseUpdateForm(initial=_course_to_form_data(course))
        return render(request, self.template_name, {"form": form, "course": course})

    def post(self, request, course_id):
        course = course_get(course_id=course_id)

        form = CourseUpdateForm(data=request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form, "course": course}, status=400)

        course_update(course_id=course.id, **form.cleaned_data)

        return redirect("courses:detail", course_id=course.id)
```

### 6.9 Serializzazione avanzata / contesto "pesante"

Nelle API la guida originale usa funzioni di serializzazione per ottimizzare le query.
Con i template il ruolo equivalente è svolto dal selector + dalla preparazione del context:

- Il selector restituisce gli oggetti con le join/prefetch necessarie
  (`select_related`, `prefetch_related`).
- La view costruisce un context con i dati calcolati già pronti per il template,
  evitando logica nel template stesso.

```python
def course_list_for_dashboard(*, user: User) -> list[Course]:
    return list(
        Course.objects.select_related("teacher")
        .prefetch_related("students")
        .filter(teacher=user)
        .order_by("-created_at")
    )
```

### 6.10 Regole per i template

- I template fanno **solo presentazione**: niente logica di dominio, niente query.
- Usare `{% extends %}`/`{% include %}` e blocchi per riusare layout e componenti.
- Template tag personalizzati **solo** per esigenze di presentazione (formattazione, micro-UI),
  mai per business logic o accesso al database.
- La logica di rendering condizionale "di dominio" (es. "l'utente può vedere X?") va risolta
  **prima**, nella view/selector, e passata al template come flag già calcolato.
- Convenzione di naming: `<app>/<modello>_<azione>.html` e template parziali con prefisso `_`
  (es. `courses/_course_card.html`).

---

## 7. URLs

Organizziamo gli URL come le views: **1 URL per view** (1 URL per azione).
Regola generale: separare gli URL di domini diversi in liste `*_patterns` e includerle da `urlpatterns`.

```python
from django.urls import include, path

from project.courses.views import (
    CourseCreateView,
    CourseDetailView,
    CourseListView,
    CourseUpdateView,
)


course_patterns = [
    path("", CourseListView.as_view(), name="list"),
    path("<int:course_id>/", CourseDetailView.as_view(), name="detail"),
    path("create/", CourseCreateView.as_view(), name="create"),
    path("<int:course_id>/update/", CourseUpdateView.as_view(), name="update"),
]

urlpatterns = [
    path("courses/", include((course_patterns, "courses"))),
]
```

Suddividere gli URL così offre flessibilità per spostare pattern di domini diversi in moduli
separati, soprattutto nei progetti grandi dove `urls.py` genera spesso conflitti di merge.

---

## 8. Settings

Quando si parla di settings tendiamo a seguire la struttura a cartelle di cookiecutter-django,
con qualche aggiustamento:

- Separiamo le impostazioni **specifiche di Django** dalle altre.
- Tutto deve essere incluso in `base.py`.
- Non deve esserci nulla di incluso **solo** in `production.py`.
- Le cose che devono funzionare solo in produzione sono controllate da variabili d'ambiente.

Struttura di riferimento:

```text
config/
├── __init__.py
├── django/
│   ├── __init__.py
│   ├── base.py
│   ├── local.py
│   ├── production.py
│   └── test.py
├── settings/
│   ├── __init__.py
│   ├── celery.py
│   ├── cors.py
│   ├── sentry.py
│   └── sessions.py
├── urls.py
├── env.py
├── wsgi.py
└── asgi.py
```

In `config/django` tutto ciò che riguarda Django:

- `base.py` contiene la maggior parte dei settings e importa tutto da `config/settings`.
- `production.py` importa da `base.py` e sovrascrive pochi settings specifici.
- `test.py` importa da `base.py` e sovrascrive pochi settings per i test
  (da usare come settings module di pytest: `DJANGO_SETTINGS_MODULE=config.django.test`).
- `local.py` importa da `base.py` e può sovrascrivere settings per lo sviluppo locale.

In `config/settings` tutto il resto: configurazione Celery, integrazioni terze, ecc.

`config/env.py`:

```python
import environ

env = environ.Env()
```

E si importa ovunque serva leggere l'ambiente:

```python
from config.env import env
```

### 8.1 Prefisso `DJANGO_`

Se sullo stesso ambiente girano altre applicazioni oltre a Django, il prefisso `DJANGO_`
aiuta a distinguere le variabili specifiche del progetto Django.
Esempio: `DJANGO_SETTINGS_MODULE`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS` hanno il prefisso;
`AWS_SECRET_KEY`, `CELERY_BROKER_URL` no. È una preferenza: l'importante è essere coerenti.

### 8.2 Integrazioni

Poiché tutto è importato in `base.py`, ma non sempre vogliamo configurare un'integrazione in locale:

- I settings dell'integrazione stanno in `config/settings/<integrazione>.py`.
- C'è sempre un booleano `USE_<INTEGRAZIONE>` letto dall'ambiente, default `False`.
- Se `True`, si procede a leggere gli altri settings, fallendo se non presenti nell'ambiente.

Esempio `config/settings/sentry.py`:

```python
from config.env import env

SENTRY_DSN = env("SENTRY_DSN", default="")

if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(dsn=SENTRY_DSN, integrations=[DjangoIntegration()])
```

### 8.3 Lettura da `.env`

Un `.env` locale è un buon modo per fornire valori ai settings. Con django-environ:

```python
import os

from config.env import env, environ

BASE_DIR = environ.Path(__file__) - 3

env.read_env(os.path.join(BASE_DIR, ".env"))
```

Due note:

- **Non committare `.env`**: farebbe trapelare credenziali.
- Committare invece un `.env.example` con valori vuoti, così i nuovi sviluppatori sanno cosa serve.

---

## 9. Errori ed eccezioni

La gestione degli errori dipende molto dal progetto: qui ci sono le linee guida generali
(adattate a un'applicazione con template, senza DRF).

### 9.1 Gerarchia di eccezioni applicative

La logica di business solleva eccezioni di un'apposita gerarchia, definita in una core app:

```python
# core/exceptions.py


class ApplicationError(Exception):
    def __init__(self, message: str, *, extra: dict | None = None):
        self.message = message
        self.extra = extra or {}
        super().__init__(message)
```

I service sollevano `ApplicationError` (o sue sottoclassi) per errori di dominio:

```python
def course_enroll(*, course: Course, user: User) -> Enrollment:
    if course.has_finished:
        raise ApplicationError("Il corso è terminato")

    enrollment = Enrollment(course=course, user=user)
    enrollment.full_clean()
    enrollment.save()
    return enrollment
```

### 9.2 Validazione e `ValidationError`

Le `django.core.exceptions.ValidationError` provengono di norma da:

- Form (validazione input).
- `full_clean` dei modelli.

Nei flussi con template la gestione è:

- **Form**: `form.is_valid()` fallisce e la view re-ndere il form con gli errori
  (il form espone `form.errors`/`field.errors` al template).
- **Model**: `full_clean()` solleva `ValidationError`; se accade dentro un service chiamato da una view,
  la view intercetta e riporta l'errore all'utente (messaggio di errore o errore di form).
- **`ApplicationError`**: va catturata nella view e mostrata come messaggio all'utente.

Pattern consigliato nella view (uso del **framework dei messaggi**):

```python
from django.contrib import messages
from django.views import View
from django.shortcuts import render, redirect

from project.core.exceptions import ApplicationError
from project.courses.forms import CourseEnrollForm
from project.courses.services import course_enroll


class CourseEnrollView(View):
    template_name = "courses/course_enroll.html"

    def post(self, request, course_id):
        form = CourseEnrollForm(data=request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form}, status=400)

        try:
            course_enroll(course_id=course_id, user=request.user, **form.cleaned_data)
        except ApplicationError as exc:
            messages.error(request, exc.message)
            return render(request, self.template_name, {"form": form}, status=400)

        messages.success(request, "Iscrizione completata.")
        return redirect("courses:detail", course_id=course_id)
```

### 9.3 Errori HTTP standard

Django gestisce da sé `Http404`, `PermissionDenied` e gli errori 5xx con pagine dedicate.
Linee guida:

- Non sollevare `Http404` dalla business logic: è una preoccupazione dell'interfaccia.
  Nei service/selector restituire `None` o sollevare eccezioni di dominio; la view decide
  se trasformare il `None` in `get_object_or_404`/`Http404`.
- Per gli errori applicativi non gestiti, loggare sempre (vedi §9.4) e non silenziare.
- Fornire template personalizzati per gli errori comuni
  (`404.html`, `403.html`, `500.html` nella cartella radice dei template) se il design lo richiede.

### 9.4 Logging

- Gli errori inattesi (5xx) devono essere **sempre loggati** e segnalati (es. Sentry), mai silenziati.
- Nelle view catturare solo le eccezioni che si sanno gestire; le altre devono propagarsi
  al middleware per essere loggate come errori veri.

---

## 10. Testing

### 10.1 Panoramica

Suddividiamo i test a seconda del tipo di codice che rappresentano.
In generale abbiamo test per: modelli, services, selectors e views.

Struttura dei file:

```text
<app>
├── __init__.py
├── tests/
│   ├── __init__.py
│   ├── factories.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── test_<nome_modello>.py
│   ├── selectors/
│   │   ├── __init__.py
│   │   └── test_<nome_selector>.py
│   ├── services/
│   │   ├── __init__.py
│   │   └── test_<nome_service>.py
│   └── views/
│       ├── __init__.py
│       └── test_<nome_view>.py
└── __init__.py
```

### 10.2 Convenzioni di naming

- File: `test_<nome_della_cosa_testata>.py`.
- Classe: `<NomeDellaCosaTestata>Tests(TestCase)`.

Esempio: dato `def a_very_neat_service(...)`, avremo:

- File: `<app>/tests/services/test_a_very_neat_service.py`
- Classe: `class AVeryNeatServiceTests(TestCase):`

Cerchiamo di rispecchiare la struttura dei moduli nella struttura dei test.

### 10.3 Services

I test dei services devono:

- Coprire la logica di business in modo **esaustivo**.
- **Colpire il database** (creare e leggere dati).
- Fare **mock** delle chiamate a task asincroni e di tutto ciò che esce dal progetto
  (email, servizi terzi, ecc.).

Per creare lo stato necessario a un test si può usare una combinazione di:

- Faker.
- Altri services per creare gli oggetti necessari.
- Factory (factory_boy).
- Semplici `Model.objects.create()`, se le factory non sono ancora state introdotte.

```python
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import TestCase

from project.payments.models import Payment
from project.payments.services import item_buy


class ItemBuyTests(TestCase):
    @patch("project.payments.services.items_get_for_user")
    def test_buying_item_that_is_already_bought_fails(self, items_get_for_user_mock):
        user = User(username="Test User")
        item = Item(name="Test Item", description="desc", price=10.15)

        items_get_for_user_mock.return_value = [item]

        with self.assertRaises(ValidationError):
            item_buy(user=user, item=item)

    @patch("project.payments.services.payment_charge.delay")
    def test_buying_item_creates_payment_and_calls_task(self, payment_charge_mock):
        user = given_a_user(username="Test user")
        item = given_a_item(name="Test Item", description="desc", price=10.15)

        self.assertEqual(0, Payment.objects.count())

        payment = item_buy(user=user, item=item)

        self.assertEqual(1, Payment.objects.count())
        self.assertEqual(payment, Payment.objects.first())
        self.assertFalse(payment.successful)

        payment_charge_mock.assert_called_once()
```

> Poiché esiste già una suite di test dedicata agli selectors, nei test dei services
> possiamo mockare gli selectors usati e fornire valori di ritorno noti.

### 10.4 Views

Le view vanno testate con il client di test di Django:

```python
from django.test import TestCase
from django.urls import reverse


class CourseListViewTests(TestCase):
    def test_list_renders_courses(self):
        course = given_a_course(name="Intro")

        response = self.client.get(reverse("courses:list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Intro")
        self.assertTemplateUsed(response, "courses/course_list.html")
```

Cosa verificare:

- Status code (200 per successo, 302 per redirect, 400 per form non valido, 404 per oggetto mancante).
- Redirect dopo le operazioni di scrittura riuscite.
- Template usato (`assertTemplateUsed`).
- Presenza/assenza di contenuti nel body HTML.
- Contenuto dei messaggi (`django.contrib.messages`) quando la view li usa.

### 10.5 Factory

Le factory sono un ottimo strumento per generare dati nei test.
Quando usate correttamente migliorano la qualità complessiva dei test.
Riferimenti:

- https://factoryboy.readthedocs.io/
- https://www.hacksoft.io/blog/improve-your-tests-django-fakes-and-factories-advanced-usage

---

## 11. Celery

Usiamo Celery per:

- Comunicare con servizi terzi (invio email, notifiche, ecc.).
- Scaricare task computazionalmente pesanti fuori dal ciclo di richiesta HTTP.
- Task periodici (Celery Beat).

### 11.1 Le basi

Trattiamo Celery come un'altra **interfaccia** verso la logica di dominio: niente business logic nei task.

```python
# tasks.py
from celery import shared_task

from project.emails.models import Email


@shared_task
def email_send(email_id: int):
    email = Email.objects.get(id=email_id)

    # Import locale: evita import circolari
    from project.emails.services import email_send

    email_send(email)
```

Il task è un'API: recupera i dati necessari e chiama il service.

Quando un service deve innescare un task:

```python
from django.db import transaction

from project.emails.tasks import email_send as email_send_task


@transaction.atomic
def user_complete_onboarding(*, user: User) -> User:
    # ... logica ...
    email = email_get_onboarding_template(user=user)

    transaction.on_commit(lambda: email_send_task.delay(email.id))

    return user
```

Punti chiave:

- I task chiamano i services.
- Il service è importato **nel corpo della funzione** del task.
- Quando vogliamo innescare un task, importiamo il task a livello di modulo con suffisso `_task`.
- I task sono eseguiti come **side effect** al commit della transazione (`transaction.on_commit`).

Questo schema previene gli import circolari, frequenti con Celery.

### 11.2 Gestione errori

La gestione degli errori (es. retry) vive nel task:

```python
from celery import shared_task
from celery.utils.log import get_task_logger

from project.emails.models import Email


logger = get_task_logger(__name__)


def _email_send_failure(self, exc, task_id, args, kwargs, einfo):
    email_id = args[0]
    email = Email.objects.get(id=email_id)

    from project.emails.services import email_failed

    email_failed(email)


@shared_task(bind=True, on_failure=_email_send_failure)
def email_send(self, email_id: int):
    email = Email.objects.get(id=email_id)

    from project.emails.services import email_send

    try:
        email_send(email)
    except Exception as exc:
        logger.warning("Exception occurred while sending email: %s", exc)
        self.retry(exc=exc, countdown=5)
```

Il callback di failure segue il pattern `_<nome_task>_failure` e chiama il service layer,
proprio come un normale task.

### 11.3 Configurazione

Seguire le linee guida ufficiali per integrare Celery con Django:
https://docs.celeryq.dev/en/stable/django/first-steps-with-django.html

### 11.4 Struttura

I task stanno in `tasks.py` dentro le app.
Stesse regole del resto: se crescono, si dividono per dominio
(`tasks/domain_a.py`, `tasks/domain_b.py`) e si importano in `tasks/__init__.py`
perché Celery possa autodiscoverarli.

### 11.5 Task periodici

Per i task periodici usiamo **Celery Beat** + `django-celery-beat` con `DatabaseScheduler`.
In più teniamo la definizione di tutti i task periodici in un **management command**
`setup_periodic_tasks`, da eseguire in fase di deploy.

```python
# <tasks_app>/management/commands/setup_periodic_tasks.py
from django.core.management.base import BaseCommand
from django.db import transaction

from django_celery_beat.models import CrontabSchedule, PeriodicTask

from project.app.tasks import some_periodic_task


class Command(BaseCommand):
    help = "Setup celery beat periodic tasks."

    @transaction.atomic
    def handle(self, *args, **kwargs):
        PeriodicTask.objects.all().delete()
        CrontabSchedule.objects.all().delete()

        periodic_tasks_data = [
            {
                "task": some_periodic_task,
                "name": "Do some periodic stuff",
                # https://crontab.guru/#15_*_*_*_*
                "cron": {
                    "minute": "15",
                    "hour": "*",
                    "day_of_week": "*",
                    "day_of_month": "*",
                    "month_of_year": "*",
                },
                "enabled": True,
            },
        ]

        for periodic_task in periodic_tasks_data:
            cron = CrontabSchedule.objects.create(**periodic_task["cron"])

            PeriodicTask.objects.create(
                name=periodic_task["name"],
                task=periodic_task["task"].name,
                crontab=cron,
                enabled=periodic_task["enabled"],
            )
```

Punti chiave:

- Il command fa parte della procedura di **deploy**.
- Mettiamo sempre il link a crontab.guru per spiegare il cron.
- Tutto è in un unico posto.
- Se si usano gli schedule "interval", leggere le note della documentazione
  di django-celery-beat sul riuso dello stesso oggetto schedule.

### 11.6 Oltre

Celery ha strumenti potenti per workflow complessi (canvas):
https://docs.celeryq.dev/en/stable/userguide/canvas.html

Finché esiste un'interfaccia ben definita verso il core dell'applicazione, si potranno
comporre task e services anche in scenari complessi.

---

## 12. Cookbook

### 12.1 Update con un service

Per gli update esiste un service generico `model_update`, usato dai service di update specifici:

```python
# common/services.py
from django.db import transaction
from django.utils import timezone


@transaction.atomic
def model_update(*, instance, fields: list[str], data: dict) -> tuple[object, bool]:
    """
    Aggiorna solo i campi indicati in `fields` con i valori in `data`.
    Usa update_fields nella save per emettere UPDATE mirati.
    """
    has_updated = False

    for field in fields:
        if field in data:
            value = data[field]
            if getattr(instance, field) != value:
                setattr(instance, field, value)
                has_updated = True

    if has_updated:
        instance.full_clean()
        instance.save(update_fields=fields)

    return instance, has_updated
```

Esempio d'uso in un service di dominio:

```python
def user_update(*, user: User, data) -> User:
    non_side_effect_fields = ["first_name", "last_name"]

    user, has_updated = model_update(
        instance=user,
        fields=non_side_effect_fields,
        data=data,
    )

    # Side-effect fields update here (es. username derivato da first & last name)
    if has_updated:
        user.set_slug_from_name()
        user.save(update_fields=["slug"])

    # ... eventuali task ...
    return user
```

> Se includi `model_update` nel progetto, porta con te anche i suoi test!

---

## 13. Template di partenza (cookiecutter)

Consigliamo di iniziare ogni nuovo progetto con un template (cookiecutter):
avere la struttura giusta fin dall'inizio ripaga.

Alcuni esempi:

- Il progetto [Django-Styleguide-Example](https://github.com/HackSoftware/Django-Styleguide-Example)
  (da cui è tratta la maggior parte degli esempi di questa guida).
- [cookiecutter-django](https://github.com/cookiecutter/cookiecutter-django), ricco di cose utili.
- Oppure creare un proprio template su misura e trasformarlo in un progetto cookiecutter.

---

## 14. DX (Developer Experience) e type annotations

Raccomandazioni per un ambiente di sviluppo piacevole:

- **uv** per environment e dipendenze (§2.1).
- **ruff** per lint/format (§2.2).
- **pytest + pytest-django** come test runner
  (settings module di test: `DJANGO_SETTINGS_MODULE=config.django.test`).
- **django-extensions** (`shell_plus`, `runserver_plus`, `show_urls`) dove utile.
- Servizi/selectors e views **annotati** con i tipi: migliorano l'autocompletamento e l'IDE.

### 14.1 django-extensions

[django-extensions](https://github.com/django-extensions/django-extensions) è una
dipendenza di sviluppo che arricchisce i management command Django. Installazione:

```bash
uv add --dev django-extensions
```

Va registrato in `INSTALLED_APPS` di `base.py` (è innocuo in produzione):

```python
INSTALLED_APPS = [
    # ...
    "django_extensions",
    # ...
]
```

Comandi più utili (da eseguire con `uv run`):

- **`shell_plus`** – shell interattiva con tutti i modelli già importati
  (niente import manuali per testare query).
  ```bash
  uv run python manage.py shell_plus
  uv run python manage.py shell_plus --ipython
  ```
- **`runserver_plus`** – dev server con page di debug/mailer e integrationi opzionali.
  ```bash
  uv run python manage.py runserver_plus
  ```
- **`show_urls`** – elenca tutte le rotte del progetto (utile per verificare i namespace).
  ```bash
  uv run python manage.py show_urls
  ```
- **`graph_models`** – genera un diagramma dei modelli.
  ```bash
  uv run python manage.py graph_models -a -o models.png
  ```

Sul fronte **type annotations / mypy**, la filosofia è:

- **Usalo se ha senso per te e ti aiuta a produrre software migliore.**
- Ci sono progetti in cui mypy è imposto e molto severo; altri dove i tipi sono più laschi.
- Il contesto comanda. In assenza di mypy, le annotazioni restano comunque obbligatorie
  per services/selectors (regole ruff `ANN`).

Configurazione di riferimento: https://github.com/typeddjango/django-stubs e
https://github.com/typeddjango/djangorestframework-stubs/

---

## 15. Risorse e riferimenti

- Django Styleguide (HackSoft): https://github.com/HackSoftware/Django-Styleguide
- Django Styleguide Example: https://github.com/HackSoftware/Django-Styleguide-Example
- Video "Django structure for scale and longevity" (Radoslav Georgiev).
- Talk DjangoCon US 2021 – "Scaling Django to 500 apps" (Dan Palmer).
- django-cookiecutter: https://github.com/cookiecutter/cookiecutter-django
- uv: https://docs.astral.sh/uv/
- ruff: https://docs.astral.sh/ruff/
- Documentazione Django: https://docs.djangoproject.com/

---

## 16. Note di manutenzione

- Questa guida è **generica e riutilizzabile**: non deve contenere riferimenti al dominio di un
  progetto specifico.
- Per convenzioni specifiche di un progetto (modello dati, flussi, glossario) fare riferimento
  ai documenti di progetto dedicati (es. `FLUSSI.md`).
- Quando una sezione non si applica al progetto corrente (es. Celery), si applica comunque ai
  progetti futuri che adotteranno questa guida.
