from django.db.models import QuerySet
from rest_framework.request import Request
from rest_framework.filters import BaseFilterBackend
from rest_framework.settings import api_settings
from rest_framework.views import View
NON_FILTER_RELATED_QUERY_PARAMS = [
    'page', 'page_size',
    api_settings.SEARCH_PARAM,
    api_settings.ORDERING_PARAM
]


class URLFilterBackend(BaseFilterBackend):
    def get_filter_query_params(self, view: View) -> dict:
        query_params = view.request.query_params.dict()
        filter_fields = getattr(view, "filter_fields", set())
        filter_query_params = {}
        for key, value in query_params.items():
            if key not in NON_FILTER_RELATED_QUERY_PARAMS:
                if key in filter_fields:
                    filter_query_params[key] = value
        return filter_query_params

    def filter_queryset(self, request: Request, queryset: QuerySet, view: View) -> QuerySet:
        query_params = self.get_filter_query_params(view)
        return queryset.filter(**query_params)
