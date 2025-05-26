import functools
from rest_framework.response import Response
from .exceptions import (
    AlreadyInFavorites, NotInFavorites, AlreadyInShoppingCart, NotInShoppingCart,
    AlreadySubscribed, NotSubscribed, CannotSubscribeToYourself, EmptyShoppingCart
)

CUSTOM_API_EXCEPTIONS = (
    AlreadyInFavorites, NotInFavorites, AlreadyInShoppingCart, NotInShoppingCart,
    AlreadySubscribed, NotSubscribed, CannotSubscribeToYourself, EmptyShoppingCart
)

def handle_api_errors(view_func):
    @functools.wraps(view_func)
    def _wrapped_view(self, request, *args, **kwargs):
        try:
            return view_func(self, request, *args, **kwargs)
        except CUSTOM_API_EXCEPTIONS as exc:
            return Response({'errors': str(exc.detail)}, status=exc.status_code)
    return _wrapped_view
