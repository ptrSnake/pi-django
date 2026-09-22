# Django Style Guide

> **Reference document for developing server-rendered Django projects.**
> The guide is reusable for any Django project: it contains no references to a specific domain.
> It is inspired by the general ideas and conventions of the [Django Styleguide](https://github.com/HackSoftware/Django-Styleguide)
> by HackSoft, independently written for projects that use **Django templates** (class-based views + forms)
> instead of an API (DRF).
>
> Status: **v1.0** – reference document for the current project and future ones.

---

## 1. What it is and how to use it

- It is **pragmatic**: everything described here has been proven in production.
- It is **opinionated**: it is *our* way of building Django applications.
- **It is not the only way**: other valid approaches exist for structuring a Django project.

When using the guide there are three general paths:

1. Follow everything written here to the letter.
2. **Choose what works for your context (recommended).**
3. Follow nothing written here.

The advice is point 2: read the guide, decide what works for your case, and adapt.

### 1.1 Key principle

Business logic must live in:

- **Services** – functions that mainly *write* data to the database.
- **Selectors** – functions that mainly *read* data from the database.
- **Model properties** (with some exceptions).
- **Model `clean` method** for additional validation (with some exceptions).

Business logic must **not** live in:

- Views.
- Forms.
- Template tags.
- Model `save` method.
- Custom managers or querysets.
- Signals.

### 1.2 Why not put logic in models / managers / querysets?

Custom managers and querysets are powerful tools and should be used to expose better interfaces on models.
But they should not be used as a container for all business logic because:

- Business logic has its own domain, not always mapped one-to-one onto the data model.
- Logic often spans multiple models: where do we put logic that touches models A, B, C and D?
- There can be calls to third-party systems: we do not want them inside a manager.

The idea is to keep the domain **separated** from the data model and the interface layer (views/forms/templates).
Combining custom querysets/managers with the idea of a separated domain gives us what we call the **service layer**.
Services can be functions, classes, modules: whatever makes sense in the specific case.

### 1.3 Why not put logic in signals?

Of all the available options, this is perhaps the one that most quickly leads to a bad situation:

- Signals are great for connecting things that *should not know about each other*.
- They are great for handling cache invalidation outside of business logic.
- If we start using them for tightly coupled things, we make the connection **implicit** and harder to trace.

Advice: use signals only for very particular use cases, not for structuring the domain.

### 1.4 General conventions

Cross-cutting rules applied to **everything** in the project.

**Code language — English only.**

- All names – variables, functions, classes, methods, models, tables, fields, constants – are **in English**.
- Docstrings and comments are **in English**.
- Error messages, model `verbose_name`/`verbose_name_plural`, and technical texts are **in English**.
- The end-user language (UI) is independent: text shown in templates can be any language,
  but identifiers, comments, and internal messages cannot.
- This document itself is in English, and every code fragment it contains is **in English**.

Example (correct):

```python
def order_cancel(*, order: Order) -> Order:  # ok
    ...
```

Example (wrong):

```python
def cancella_ordine(*, ordine: Ordine) -> Ordine:  # wrong
    ...
```

**Identifiers – UUID as primary key.**

- Every model has a **UUID primary key** and **no auto-increment integer `id`**.
- The PK field is named `id` and is a `UUIDField(primary_key=True, default=uuid.uuid4, editable=False)`.
- All ForeignKeys point to the UUID key of the referenced model.
- Parameters that receive an identifier (e.g. `user_id`, `order_id`) are of type `uuid.UUID`, not `int`.
- This applies to all models, including user models and domain models.

---

## 2. Tooling: uv and ruff

> All new projects start with **uv** for dependency and environment management and with **ruff**
> as the single tool for linting **and** formatting.

### 2.1 uv

[uv](https://docs.astral.sh/uv/) is the Python project/dependency manager used by default.

Usage rules:

- Initialize the project with `uv init` and add Django with `uv add django`.
- Declare the required Python version in `[project].requires-python` of `pyproject.toml`
  and in the `.python-version` file (created by `uv`).
- The `uv.lock` file guarantees reproducible environments and is **always** committed.
- All commands are run with `uv run`:

```bash
uv run python manage.py runserver
uv run python manage.py migrate
uv run ruff check .
uv run ruff format .
uv run pytest
```

- For development dependencies (ruff, pytest, factory-boy, etc.) use the dedicated group:

```bash
uv add --dev ruff pytest factory-boy
```

- Do not install packages "blindly" into the global environment: everything goes through `pyproject.toml`.

### 2.2 ruff

[ruff](https://docs.astral.sh/ruff/) is the single tool for linting, formatting, and import sorting.

Usage rules:

- **`ruff check`** for linting.
- **`ruff format`** for formatting (Black style).
- Configuration in `[tool.ruff]` of `pyproject.toml`; minimal example:

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
    "D",    # pydocstyle (optional)
]

[tool.ruff.lint.isort]
known-first-party = ["config", "<project_name>"]
```

- Before every commit: `uv run ruff check . && uv run ruff format --check .`.
- **Import sorting**: imports must be sorted with rule `I` (isort): first stdlib, then third-party,
  then Django, then the project's local modules. Never sort by hand.
- **Type annotations**: services and selectors use *keyword-only arguments* and are annotated
  (rule `ANN`). Annotations are mandatory even if you do not use mypy.
- Using mypy is **optional** and depends on the project (see §14).

---

## 3. Models

Models must take care of the data model and not much else.

### 3.1 Base model

It is good practice to define a `BaseModel` to inherit from.
Besides the **UUID** primary key (mandatory per §1.4), fields like `created_at` and `updated_at`
are perfect candidates:

```python
import uuid

from django.db import models
from django.utils import timezone


class BaseModel(models.Model):
    # UUID primary key: no auto-increment integer id (§1.4).
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    created_at = models.DateTimeField(db_index=True, default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
```

Then every model inherits from `BaseModel`:

```python
class SomeModel(BaseModel):
    pass
```

Note: since `BaseModel` already defines the UUID primary key, the practical effect is that
all models that inherit from it use UUID as their key. Keep `DEFAULT_AUTO_FIELD` on its default
(`BigAutoField`) for anything else: Django's M2M through models require an `AutoField`
subclass and `UUIDField` is not one.

### 3.2 Validation – clean and full_clean

Example:

```python
class Course(BaseModel):
    name = models.CharField(unique=True, max_length=255)

    start_date = models.DateField()
    end_date = models.DateField()

    def clean(self):
        if self.start_date >= self.end_date:
            raise ValidationError("End date cannot be earlier than start date")
```

We define `clean` to guarantee correct data in the database.
For `clean` to be called, someone must invoke `full_clean` on the instance before `save`.
The advice is to do it **in the service**, right before `save`:

```python
def course_create(*, name: str, start_date: date, end_date: date) -> Course:
    obj = Course(name=name, start_date=start_date, end_date=end_date)

    obj.full_clean()
    obj.save()

    return obj
```

General rules on when to validate in `clean`:

- When validation concerns several **non-relational** fields of the model.
- When the validation is simple enough.

Move validation to the service layer when:

- The validation logic is more complex.
- Cross-cutting relationships or additional data fetches are needed.

Having validation both in `clean` and in the service is acceptable, but we tend to move things to the service.

### 3.3 Validation – constraints

If a validation can be expressed with Django constraints, prefer that: less code to write and maintain,
and the database protects the data even when it is inserted from another point.

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

Note: since **Django 4.1**, calling `full_clean` also checks the model constraints,
so in the service you get a clean `ValidationError` instead of an `IntegrityError`.
If you go through `Model.objects.create(...)` instead, the downside remains (you get an `IntegrityError`).

Useful documentation:

- https://docs.djangoproject.com/en/stable/ref/models/constraints/
- https://www.pythonmorsels.com/ (Adam Johnson's CheckConstraint articles)

### 3.4 Properties

Properties are a great way to quickly access a derived value of the instance:

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

General rules for adding properties to a model:

- A simple derived value is needed, based on **non-relational** fields: add a `@property`.
- The derived value calculation is simple enough.

The property must become something else (service, selector, utility) when:

- Traversing multiple relationships or additional data fetches is required.
- The calculation is more complex.

Rules are deliberately vague: context matters, use common sense.

### 3.5 Methods

Methods build on properties when an argument is needed:

```python
def is_within(self, x: date) -> bool:
    return self.start_date <= x <= self.end_date
```

`is_within` cannot be a property because it requires an argument → it is a method.

Another typical use of methods: setting attributes where setting one always requires
the derived setting of another:

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

General rules:

- A simple derived value that requires arguments, based on non-relational fields → method.
- Setting an attribute always requires derived values on other attributes → method.
- Traversing relationships / fetching data or a complex calculation → service/selector/utility.

### 3.6 Testing models

Models should only be tested if they have something more (validation, properties, methods):

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

Notes:

- We verify that a `ValidationError` is raised by calling `full_clean`.
- **The database is not touched**: in many cases it is not needed, and this speeds up the tests.

---

## 4. Services

Services are where business logic lives.
The service layer speaks the language of the domain, can access the database and other resources,
and can interact with other parts of the system.

A service can be:

- A simple function.
- A class.
- A whole module.
- Whatever makes sense in the specific case.

In most cases a service is a simple function that:

- Lives in the `<app>/services.py` module.
- Takes **keyword-only arguments only**, unless it requires zero or one argument.
- Is type-annotated (even if you do not use mypy right now).
- Interacts with the database, resources, and other parts of the system.
- Does business logic: from simple model creation to complex cross-cutting problems,
  up to calling external services and tasks.

### 4.1 Example – function service

```python
def user_create(*, email: str, name: str) -> User:
    user = User(email=email)
    user.full_clean()
    user.save()

    profile_create(user=user, name=name)
    confirmation_email_send(user=user)

    return user
```

As you can see, this service calls two other services – `profile_create` and `confirmation_email_send`.
Everything related to user creation is in a single place and can be traced.

### 4.2 Example – class service

We can have "class" services: an elegant way to encapsulate multiple behaviors under a namespace.

```python
from django.db import transaction
from django.utils import timezone


class FileUploadService:
    """
    Example of a service class encapsulating create & update under a namespace.
    The class serves for:
    1. The namespace.
    2. The reuse of `_infer_file_name_and_type`.
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

Class services are also suited for **flows**: things that span multiple steps.

### 4.3 Naming convention

The pattern is **`<entity>_<action>`**, e.g. `user_create`, `course_update`, `order_cancel`.
It may seem strange at first, but it has concrete benefits:

- **Namespacing**: it is easy to find all services starting with `user_`, and it makes sense
  to group them in a `users.py` module.
- **Greppability**: to see all actions on an entity, just search `grep "user_"`.

### 4.4 Modules

If the app is simple, all services live in `services.py`.
When the file grows, split it into a folder with submodules per subdomain:

```text
services/
├── __init__.py
├── jwt.py
└── oauth.py
```

You can do the import-export in `services/__init__.py` to keep importing from
`project.authentication.services`, or create module folders (`jwt/__init__.py`) and put the code there.
The structure is at your discretion: when you feel it is time to restructure, do it.

---

## 5. Selectors

In most projects we distinguish between "writing data" and "reading data":

- **Services** handle writing.
- **Selectors** handle reading.

Selectors can be seen as a *sub-layer* of services, specialized in fetching.
If this idea does not resonate, you can use services for both operations.

A selector follows the same rules as a service (keyword-only, annotated, etc.).

Example in the `<app>/selectors.py` module:

```python
def user_list(*, fetched_by: User) -> Iterable[User]:
    visible_ids = user_get_visible_for(user=fetched_by)
    return User.objects.filter(id__in=visible_ids)
```

You can return querysets, lists, or whatever makes sense in the specific case.
**Filtering** (search, parameters) is the selector's responsibility.

### 5.1 Filtering with django-filter

To handle list search/filtering we use **django-filter**.

- Each app has a **`filters.py`** module with `FilterSet` classes dedicated to its models.
- The filter class defines the filterable fields and their logic (exact lookups,
  icontains, choice, range, etc.).
- The selector receives the filter parameters (dict or `request.GET`), applies the `FilterSet`
  to the queryset, and returns the result.

Example of `users/filters.py`:

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

Example of a selector that uses the filter:

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

Rules:

- The `FilterSet` exposes **only** the filterable fields, never the whole queryset.
- The filter responsibility stays with the selector: the `FilterSet` is a means, not an end.
- For list views, the view passes `request.GET` as `filters` (see §6.4).

### 5.2 How to build a list query

Complete recipe for building a filtered, ordered, and paginated list,
from the `FilterSet` to the template.

#### 5.2.1 Available filter types

`django-filter` exposes a `Filter` per field type; `lookup_expr` accepts
the same lookups as Django (`exact`, `icontains`, `in`, `gte`, `lte`, `range`, ...).

| Filter | Typical use |
|---|---|
| `CharFilter` | Text search: `CharFilter(lookup_expr="icontains")` |
| `BooleanFilter` | Boolean flags (e.g. `is_active`) |
| `NumberFilter` | Exact numeric values |
| `DateFilter` / `DateTimeFilter` | Dates and datetimes |
| `ChoiceFilter` | Field with `choices` |
| `ModelChoiceFilter` | Single FK (dropdown select) |
| `ModelMultipleChoiceFilter` | Multiple FK |
| `BaseInFilter` | `in` lookup (e.g. `NumberFilter` + `BaseInFilter`) |
| `RangeFilter` | `range` lookup (e.g. date intervals) |
| `OrderingFilter` | Client-side ordering |

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

#### 5.2.2 Conventions and best practices

- A **`filters.py`** module per app, a **`<Model>Filter`** class per model.
- `Meta.fields = []` and **explicitly declared** fields: the `FilterSet` exposes
  only what you declare, never the whole queryset.
- One `Filter` per field, with explicit `field_name` and `lookup_expr`
  (e.g. `joined_after` on `date_joined` with `gte`).
- The **filter responsibility stays in the selector**: the `FilterSet` is a means,
  not an end; authorization logic (e.g. excluding superusers) lives in the selector.
- Always present guard: `filters = filters or {}`.
- **Default ordering in the selector** (`order_by`), not in the `FilterSet`.
- **Pagination in the selector**, which returns Django's `Page` (see §6.4).
- The view passes `request.GET` as `filters` and reads `page` from the querystring.

#### 5.2.3 End-to-end recipe (with pagination)

1. **`users/filters.py`** – define the filterable fields:

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

2. **`users/selectors.py`** – the selector applies filter, ordering, and pagination:

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

3. **`users/views.py`** – the view acts as a bridge: selector + context:

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

4. **`users/urls.py`** – one route per view (see §7):

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

5. **`users/templates/users/user_list.html`** – presentation only: the page
   receives `page` with the filter querystring already active, so the
   pagination links must preserve it (e.g. `?email=x&page=2`):

```html
<form method="get">
  <input type="text" name="email" placeholder="Email">
  <input type="text" name="name" placeholder="Name">
  <button type="submit">Search</button>
</form>

<ul>
  {% for user in page.object_list %}
    <li>{{ user.email }} – {{ user.name }}</li>
  {% empty %}
    <li>No users found.</li>
  {% endfor %}
</ul>

{% if page.has_other_pages %}
  <nav>
    {% if page.has_previous %}
      <a href="?{{ request.GET.urlencode }}&page={{ page.previous_page_number }}">Previous</a>
    {% endif %}
    <span>Page {{ page.number }} of {{ page.paginator.num_pages }}</span>
    {% if page.has_next %}
      <a href="?{{ request.GET.urlencode }}&page={{ page.next_page_number }}">Next</a>
    {% endif %}
  </nav>
{% endif %}
```

Recipe rules:

- The `FilterSet` handles **only** filtering; ordering and pagination are the selector's.
- The selector returns a `Page`; the view passes it to the template without further logic.
- The template makes no queries and contains no domain logic: only loops and pagination links.

---

## 6. Views and Templates

> This section replaces the "APIs & Serializers" section of the original styleguide,
> because the reference projects render **Django templates** and do not expose an API.
> DRF is not used: no serializers, no `APIView`.

### 6.1 Principles

Views are **the interface** to the domain logic. General rules:

- **One view per operation** (for CRUD on a model: list, detail, create, update, delete).
- Inherit from the simplest view: `django.views.View`.
- Avoid abstract *generic* classes (`ListView`, `CreateView`, ...): they tend to handle things
  through forms/querysets implicitly, and we want to do it explicitly via services/selectors.
- **No business logic in the view.**
- The view can do the object *fetch* or data preparation, but the logic goes into the services.

The view is a thin shell bridging the HTTP request, the domain logic, and the template.

### 6.2 Input and output

- **Input**: validating incoming data is the job of a dedicated **Form** (`django.forms.Form` or `ModelForm`).
  The form validates and the cleaned data is passed to the service.
- **Output**: there are no serializers. The view passes to the template the data returned by the selector
  (objects, querysets, computed values) in the `render` *context*.

Recurring schema for every operation:

1. The view receives the request.
2. (optional) A dedicated Form validates the input.
3. The view calls a **selector** (read) or a **service** (write).
4. The view renders a **template** with the data in the context; on error, re-renders the form with errors.

### 6.3 Naming convention

- Views: **`<Entity><Action>View`** → `CourseList`, `CourseDetail`, `CourseCreate`, `CourseUpdate`.
- Forms: **`<Entity><Action>Form`** → `CourseCreateForm`, `CourseUpdateForm`.
- Templates: **`<app>/<model>_<action>.html`** → `courses/course_list.html`, `courses/course_create.html`.

### 6.4 List (with filter and pagination)

The view calls a selector that applies filtering and pagination and passes the results to the template.

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

> The key point: **filtering is the selector's responsibility**.
> `FilterSet`s live in the app's `filters.py` module and are consumed by selectors
> (see §5.1).
> The same principle applies to pagination: if needed, paginate inside the selector
> (e.g. with `django.core.paginator.Paginator`).

Example of a view with pagination inside the logic:

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

### 6.6 Fetching objects

When a view receives an id, where is the object fetched? Options:

- Fetch it in the view with a `get_object` utility and pass it to the service/selector.
- Pass the id to the service/selector and fetch it there.

The choice depends on the context; what matters is **consistency**. Typical pattern:

```python
from django.shortcuts import get_object_or_404

from project.courses.models import Course


def course_get(*, course_id: int) -> Course:
    return get_object_or_404(Course, id=course_id)
```

`get_object_or_404` raises `Http404`, which Django turns into the "Not found" page.

### 6.7 Create (with form + service)

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

Same schema as create, with the update service. The form can have partial fields:

```python
class CourseUpdateForm(forms.Form):
    name = forms.CharField(max_length=255, required=False)
    start_date = forms.DateField(required=False)
    end_date = forms.DateField(required=False)
```

The view fetches the object, validates the form, and calls the service:

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

### 6.9 Advanced serialization / "heavy" context

In APIs the original guide uses serialization functions to optimize queries.
With templates, the equivalent role is played by the selector + context preparation:

- The selector returns the objects with the needed joins/prefetches
  (`select_related`, `prefetch_related`).
- The view builds a context with computed data already ready for the template,
  avoiding logic in the template itself.

```python
def course_list_for_dashboard(*, user: User) -> list[Course]:
    return list(
        Course.objects.select_related("teacher")
        .prefetch_related("students")
        .filter(teacher=user)
        .order_by("-created_at")
    )
```

### 6.10 Template rules

- Templates do **presentation only**: no domain logic, no queries.
- Use `{% extends %}`/`{% include %}` and blocks to reuse layouts and components.
- Custom template tags **only** for presentation needs (formatting, micro-UI),
  never for business logic or database access.
- Conditional "domain" rendering logic (e.g. "can the user see X?") must be resolved
  **beforehand**, in the view/selector, and passed to the template as a precomputed flag.
- Naming convention: `<app>/<model>_<action>.html` and partial templates with `_` prefix
  (e.g. `courses/_course_card.html`).

---

## 7. URLs

We organize URLs like views: **1 URL per view** (1 URL per action).
General rule: separate URLs of different domains into `*_patterns` lists and include them from `urlpatterns`.

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

Splitting URLs this way gives flexibility to move patterns of different domains into separate
modules, especially in large projects where `urls.py` often generates merge conflicts.

---

## 8. Settings

For settings we tend to follow cookiecutter-django's folder structure, with a few adjustments:

- We separate **Django-specific** settings from the others.
- Everything must be included in `base.py`.
- Nothing should be included **only** in `production.py`.
- Things that must work only in production are controlled by environment variables.

Reference structure:

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

In `config/django`, everything that concerns Django:

- `base.py` contains most of the settings and imports everything from `config/settings`.
- `production.py` imports from `base.py` and overrides a few environment-specific settings.
- `test.py` imports from `base.py` and overrides a few settings for tests
  (use it as pytest's settings module: `DJANGO_SETTINGS_MODULE=config.django.test`).
- `local.py` imports from `base.py` and may override settings for local development.

In `config/settings`, everything else: Celery configuration, third-party integrations, etc.

`config/env.py`:

```python
import environ

env = environ.Env()
```

And it is imported wherever the environment needs to be read:

```python
from config.env import env
```

### 8.1 `DJANGO_` prefix

If other applications run on the same environment besides Django, the `DJANGO_`
prefix helps distinguish the variables specific to the Django project.
Example: `DJANGO_SETTINGS_MODULE`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS` have the prefix;
`AWS_SECRET_KEY`, `CELERY_BROKER_URL` do not. It is a preference: the important thing is to be consistent.

### 8.2 Integrations

Since everything is imported in `base.py`, but we do not always want to configure an integration locally:

- The integration settings live in `config/settings/<integration>.py`.
- There is always a `USE_<INTEGRATION>` boolean read from the environment, default `False`.
- If `True`, the other settings are read, failing if they are not present in the environment.

Example `config/settings/sentry.py`:

```python
from config.env import env

SENTRY_DSN = env("SENTRY_DSN", default="")

if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(dsn=SENTRY_DSN, integrations=[DjangoIntegration()])
```

### 8.3 Reading from `.env`

A local `.env` is a good way to provide values to the settings. With django-environ:

```python
import os

from config.env import env, environ

BASE_DIR = environ.Path(__file__) - 3

env.read_env(os.path.join(BASE_DIR, ".env"))
```

Two notes:

- **Never commit `.env`**: it would leak credentials.
- Commit a `.env.example` with empty values instead, so new developers know what is needed.

---

## 9. Errors and exceptions

Error handling depends a lot on the project: here are the general guidelines
(adapted to a template application, without DRF).

### 9.1 Application exception hierarchy

Business logic raises exceptions from a dedicated hierarchy, defined in a core app:

```python
# core/exceptions.py


class ApplicationError(Exception):
    def __init__(self, message: str, *, extra: dict | None = None):
        self.message = message
        self.extra = extra or {}
        super().__init__(message)
```

Services raise `ApplicationError` (or its subclasses) for domain errors:

```python
def course_enroll(*, course: Course, user: User) -> Enrollment:
    if course.has_finished:
        raise ApplicationError("The course has ended")

    enrollment = Enrollment(course=course, user=user)
    enrollment.full_clean()
    enrollment.save()
    return enrollment
```

### 9.2 Validation and `ValidationError`

`django.core.exceptions.ValidationError` usually comes from:

- Forms (input validation).
- Model `full_clean`.

In template flows the handling is:

- **Form**: `form.is_valid()` fails and the view re-renders the form with errors
  (the form exposes `form.errors`/`field.errors` to the template).
- **Model**: `full_clean()` raises `ValidationError`; if it happens inside a service called by a view,
  the view catches it and reports the error to the user (error message or form error).
- **`ApplicationError`**: must be caught in the view and shown to the user as a message.

Recommended pattern in the view (using the **messages framework**):

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

        messages.success(request, "Enrollment completed.")
        return redirect("courses:detail", course_id=course_id)
```

### 9.3 Standard HTTP errors

Django handles `Http404`, `PermissionDenied`, and 5xx errors itself with dedicated pages.
Guidelines:

- Do not raise `Http404` from business logic: it is an interface concern.
  In services/selectors return `None` or raise domain exceptions; the view decides
  whether to turn the `None` into `get_object_or_404`/`Http404`.
- For unhandled application errors, always log (see §9.4) and never silence them.
- Provide custom templates for common errors
  (`404.html`, `403.html`, `500.html` in the root templates folder) if the design requires it.

### 9.4 Logging

- Unexpected errors (5xx) must be **always logged** and reported (e.g. Sentry), never silenced.
- In views, catch only the exceptions you know how to handle; the others must propagate
  to the middleware to be logged as real errors.

---

## 10. Testing

### 10.1 Overview

We split tests according to the type of code they represent.
In general we have tests for: models, services, selectors, and views.

File structure:

```text
<app>
├── __init__.py
├── tests/
│   ├── __init__.py
│   ├── factories.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── test_<model_name>.py
│   ├── selectors/
│   │   ├── __init__.py
│   │   └── test_<selector_name>.py
│   ├── services/
│   │   ├── __init__.py
│   │   └── test_<service_name>.py
│   └── views/
│       ├── __init__.py
│       └── test_<view_name>.py
└── __init__.py
```

### 10.2 Naming conventions

- File: `test_<name_of_the_things_tested>.py`.
- Class: `<NameOfTheThingTested>Tests(TestCase)`.

Example: given `def a_very_neat_service(...)`, we will have:

- File: `<app>/tests/services/test_a_very_neat_service.py`
- Class: `class AVeryNeatServiceTests(TestCase):`

We try to mirror the module structure in the test structure.

### 10.3 Services

Service tests must:

- Cover the business logic **exhaustively**.
- **Hit the database** (create and read data).
- **Mock** calls to async tasks and anything that leaves the project
  (email, third-party services, etc.).

To create the state needed for a test you can use a combination of:

- Faker.
- Other services to create the needed objects.
- Factories (factory_boy).
- Plain `Model.objects.create()`, if factories have not been introduced yet.

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

> Since a dedicated test suite for selectors already exists, in service tests
> we can mock the selectors used and provide known return values.

### 10.4 Views

Views are tested with Django's test client:

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

What to verify:

- Status code (200 for success, 302 for redirect, 400 for invalid form, 404 for missing object).
- Redirect after successful write operations.
- Template used (`assertTemplateUsed`).
- Presence/absence of content in the HTML body.
- Content of messages (`django.contrib.messages`) when the view uses them.

### 10.5 Factories

Factories are a great tool for generating test data.
When used correctly they improve the overall quality of the tests.
References:

- https://factoryboy.readthedocs.io/
- https://www.hacksoft.io/blog/improve-your-tests-django-fakes-and-factories-advanced-usage

---

## 11. Celery

We use Celery to:

- Communicate with third-party services (sending emails, notifications, etc.).
- Offload computationally heavy tasks from the HTTP request cycle.
- Run periodic tasks (Celery Beat).

### 11.1 The basics

We treat Celery as another **interface** to the domain logic: no business logic in tasks.

```python
# tasks.py
from celery import shared_task

from project.emails.models import Email


@shared_task
def email_send(email_id: int):
    email = Email.objects.get(id=email_id)

    # Local import: avoids circular imports
    from project.emails.services import email_send

    email_send(email)
```

The task is an API: it fetches the needed data and calls the service.

When a service must trigger a task:

```python
from django.db import transaction

from project.emails.tasks import email_send as email_send_task


@transaction.atomic
def user_complete_onboarding(*, user: User) -> User:
    # ... logic ...
    email = email_get_onboarding_template(user=user)

    transaction.on_commit(lambda: email_send_task.delay(email.id))

    return user
```

Key points:

- Tasks call services.
- The service is imported **inside the body of the task function**.
- When we want to trigger a task, we import the task at module level with the `_task` suffix.
- Tasks are executed as a **side effect** of the transaction commit (`transaction.on_commit`).

This pattern prevents the circular imports that are frequent with Celery.

### 11.2 Error handling

Error handling (e.g. retry) lives in the task:

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

The failure callback follows the `_<task_name>_failure` pattern and calls the service layer,
just like a normal task.

### 11.3 Configuration

Follow the official guidelines for integrating Celery with Django:
https://docs.celeryq.dev/en/stable/django/first-steps-with-django.html

### 11.4 Structure

Tasks live in `tasks.py` inside the apps.
Same rules as the rest: if they grow, split them by domain
(`tasks/domain_a.py`, `tasks/domain_b.py`) and import them in `tasks/__init__.py`
so that Celery can autodiscover them.

### 11.5 Periodic tasks

For periodic tasks we use **Celery Beat** + `django-celery-beat` with the `DatabaseScheduler`.
Additionally, we keep the definition of all periodic tasks in a **management command**
`setup_periodic_tasks`, to run at deploy time.

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

Key points:

- The command is part of the **deploy** procedure.
- We always add the crontab.guru link to explain the cron.
- Everything is in a single place.
- If you use "interval" schedules, read the django-celery-beat documentation notes
  about reusing the same schedule object.

### 11.6 Beyond

Celery has powerful tools for complex workflows (canvas):
https://docs.celeryq.dev/en/stable/userguide/canvas.html

As long as a well-defined interface to the application core exists, you can keep
composing tasks and services even in complex scenarios.

---

## 12. Cookbook

### 12.1 Update with a service

For updates there is a generic `model_update` service, used by the specific update services:

```python
# common/services.py
from django.db import transaction
from django.utils import timezone


@transaction.atomic
def model_update(*, instance, fields: list[str], data: dict) -> tuple[object, bool]:
    """
    Updates only the fields listed in `fields` with the values in `data`.
    Uses update_fields in save to emit targeted UPDATE statements.
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

Usage example in a domain service:

```python
def user_update(*, user: User, data) -> User:
    non_side_effect_fields = ["first_name", "last_name"]

    user, has_updated = model_update(
        instance=user,
        fields=non_side_effect_fields,
        data=data,
    )

    # Side-effect fields update here (e.g. username derived from first & last name)
    if has_updated:
        user.set_slug_from_name()
        user.save(update_fields=["slug"])

    # ... possible tasks ...
    return user
```

> If you include `model_update` in the project, bring its tests along too!

---

## 13. Starting template (cookiecutter)

We recommend starting every new project with a template (cookiecutter):
having the right structure from the beginning pays off.

Some examples:

- The project [Django-Styleguide-Example](https://github.com/HackSoftware/Django-Styleguide-Example)
  (from which most of the examples in this guide are taken).
- [cookiecutter-django](https://github.com/cookiecutter/cookiecutter-django), full of useful things.
- Or create your own tailored template and turn it into a cookiecutter project.

---

## 14. DX (Developer Experience) and type annotations

Recommendations for a pleasant development environment:

- **uv** for environment and dependencies (§2.1).
- **ruff** for lint/format (§2.2).
- **pytest + pytest-django** as the test runner
  (test settings module: `DJANGO_SETTINGS_MODULE=config.django.test`).
- **django-extensions** (`shell_plus`, `runserver_plus`, `show_urls`) where useful.
- Services/selectors and views **annotated** with types: improves autocompletion and IDE support.

### 14.1 django-extensions

[django-extensions](https://github.com/django-extensions/django-extensions) is a
development dependency that enriches Django management commands. Installation:

```bash
uv add --dev django-extensions
```

It must be registered in `INSTALLED_APPS` of `base.py` (it is harmless in production):

```python
INSTALLED_APPS = [
    # ...
    "django_extensions",
    # ...
]
```

Most useful commands (run with `uv run`):

- **`shell_plus`** – interactive shell with all models already imported
  (no manual imports to test queries).
  ```bash
  uv run python manage.py shell_plus
  uv run python manage.py shell_plus --ipython
  ```
- **`runserver_plus`** – dev server with debug/mailer page and optional integrations.
  ```bash
  uv run python manage.py runserver_plus
  ```
- **`show_urls`** – lists all project routes (useful for checking namespaces).
  ```bash
  uv run python manage.py show_urls
  ```
- **`graph_models`** – generates a model diagram.
  ```bash
  uv run python manage.py graph_models -a -o models.png
  ```

On the **type annotations / mypy** front, the philosophy is:

- **Use it if it makes sense for you and helps you produce better software.**
- Some projects enforce mypy and are very strict; others have looser typing.
- Context decides. In the absence of mypy, annotations remain mandatory anyway
  for services/selectors (ruff `ANN` rules).

Reference configuration: https://github.com/typeddjango/django-stubs and
https://github.com/typeddjango/djangorestframework-stubs/

---

## 15. Resources and references

- Django Styleguide (HackSoft): https://github.com/HackSoftware/Django-Styleguide
- Django Styleguide Example: https://github.com/HackSoftware/Django-Styleguide-Example
- Video "Django structure for scale and longevity" (Radoslav Georgiev).
- DjangoCon US 2021 talk – "Scaling Django to 500 apps" (Dan Palmer).
- django-cookiecutter: https://github.com/cookiecutter/cookiecutter-django
- uv: https://docs.astral.sh/uv/
- ruff: https://docs.astral.sh/ruff/
- Django documentation: https://docs.djangoproject.com/

---

## 16. Maintenance notes

- This guide is **generic and reusable**: it must not contain references to the domain of a
  specific project.
- For project-specific conventions (data model, flows, glossary) refer to the project's
  dedicated documents (e.g. `FLOWS.md`).
- When a section does not apply to the current project (e.g. Celery), it still applies to
  future projects that will adopt this guide.

---

## Credits and license

This guide is an **original work**, independently written for server-rendered Django projects.
It is inspired by the general ideas and conventions popularized by the
[Django Styleguide](https://github.com/HackSoftware/Django-Styleguide) by [HackSoft](https://www.hacksoft.io/)
(MIT License) — such as the services/selectors layer and its naming conventions — but it is not a
reproduction, translation, or adaptation of it.

- Original inspiration: https://github.com/HackSoftware/Django-Styleguide
- This guide: Copyright (c) 2026 ptrSnake, MIT License.

MIT License full text: see [LICENSE](../LICENSE).
