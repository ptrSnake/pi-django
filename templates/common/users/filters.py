"""FilterSets for the users app (STILE-DJANGO.md §5.1)."""

import django_filters

from users.models import User


class UserFilter(django_filters.FilterSet):
    """FilterSet exposing only the explicitly declared filterable fields."""

    email = django_filters.CharFilter(lookup_expr="icontains")
    name = django_filters.CharFilter(lookup_expr="icontains")
    is_active = django_filters.BooleanFilter()

    class Meta:
        model = User
        fields = []
