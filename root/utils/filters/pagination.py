from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class URLPagination(PageNumberPagination):
    page_size_query_param = "page_size"

    def get_page_number(self, request, paginator):
        page_number = request.query_params.get(self.page_query_param)
        if page_number:
            return super().get_page_number(request, paginator)

    def paginate_queryset(self, queryset, request, view=None):
        page_size = self.get_page_size(request)
        paginator = self.django_paginator_class(queryset, page_size)
        page_number = self.get_page_number(request, paginator)
        if page_size and page_number:
            return super().paginate_queryset(queryset, request, view)

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            "current": self.page.number,
            'results': data,
        })
