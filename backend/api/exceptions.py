"""Кастомные исключения для проекта."""
from rest_framework.exceptions import APIException


class CannotSubscribeToYourself(APIException):
    """Исключение при попытке подписаться на самого себя."""

    status_code = 400
    default_detail = 'Вы не можете подписаться на самого себя.'
    default_code = 'cannot_subscribe_to_yourself'


class AlreadySubscribed(APIException):
    """Исключение при попытке подписаться повторно."""

    status_code = 400
    default_detail = 'Вы уже подписаны на этого автора.'
    default_code = 'already_subscribed'


class NotSubscribed(APIException):
    """Исключение при попытке отписаться от автора без подписки."""

    status_code = 400
    default_detail = 'Вы не подписаны на этого автора.'
    default_code = 'not_subscribed'


class AlreadyInFavorites(APIException):
    """Исключение при добавлении рецепта в избранное повторно."""

    status_code = 400
    default_detail = 'Рецепт уже добавлен в избранное.'
    default_code = 'already_in_favorites'


class NotInFavorites(APIException):
    """Исключение при удалении рецепта из избранного, если его там нет."""

    status_code = 400
    default_detail = 'Рецепта нет в избранном.'
    default_code = 'not_in_favorites'


class AlreadyInShoppingCart(APIException):
    """Исключение при добавлении рецепта в список покупок повторно."""

    status_code = 400
    default_detail = 'Рецепт уже добавлен в список покупок.'
    default_code = 'already_in_shopping_cart'


class NotInShoppingCart(APIException):
    """Исключение при удалении рецепта из списка покупок, если его там нет."""

    status_code = 400
    default_detail = 'Рецепта нет в списке покупок.'
    default_code = 'not_in_shopping_cart'


class EmptyShoppingCart(APIException):
    """Исключение при попытке скачать пустой список покупок."""

    status_code = 400
    default_detail = 'Список покупок пуст.'
    default_code = 'empty_shopping_cart'
