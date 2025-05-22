"""Пагинация для API."""
from rest_framework.pagination import PageNumberPagination


class CustomPagination(PageNumberPagination):
    """Кастомная пагинация для API."""

    page_size_query_param = 'limit'
    page_size = 6
