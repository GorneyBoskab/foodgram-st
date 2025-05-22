"""Права доступа для API."""
from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.BasePermission):
    """Право доступа для автора или только для чтения."""

    def has_permission(self, request, view):
        """Проверка права доступа для запроса."""
        return (request.method in permissions.SAFE_METHODS
                or request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        """Проверка права доступа для объекта."""
        return (request.method in permissions.SAFE_METHODS
                or obj.author == request.user)
