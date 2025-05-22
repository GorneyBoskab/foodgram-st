"""
Представления для API."""
from django.db.models import Sum
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.exceptions import APIException, ValidationError

from api.filters import RecipeFilter, IngredientFilter
from api.pagination import CustomPagination
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (
    IngredientSerializer, TagSerializer,
    RecipeListSerializer, RecipeCreateSerializer,
    RecipeShortSerializer
)
from recipes.models import (
    Ingredient, Tag, Recipe, RecipeIngredient,
    Favorite, ShoppingCart
)
from recipes.utils import create_file_from_data
from api.exceptions import (
    AlreadyInFavorites, NotInFavorites,
    AlreadyInShoppingCart, NotInShoppingCart,
    EmptyShoppingCart
)
from api.utils import handle_api_errors


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Представление для ингредиентов."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    pagination_class = None  # Disable pagination for ingredients

    def retrieve(self, request, *args, **kwargs):
        pk = kwargs.get('pk')
        try:
            if isinstance(pk, str) and ("{{" in pk and "}}" in pk):
                return Response({"errors": f"Неверный ID ингредиента: {pk}"}, status=status.HTTP_400_BAD_REQUEST)
            pk = int(pk)
        except (ValueError, TypeError):
            return Response({"errors": f"Неверный формат ID ингредиента: {pk}"}, status=status.HTTP_400_BAD_REQUEST)
        obj = Ingredient.objects.filter(id=pk).first()
        if not obj:
            return Response({"errors": "Ингредиент не найден"}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(obj)
        return Response(serializer.data)

class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Представление для тегов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)


class RecipeViewSet(viewsets.ModelViewSet):
    """Представление для рецептов."""

    queryset = Recipe.objects.all()
    pagination_class = CustomPagination
    permission_classes = (IsAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    
    def get_serializer_class(self):
        """Выбор сериализатора в зависимости от запроса."""
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeCreateSerializer
        return RecipeListSerializer
    
    def get_object_or_404_with_error(self, model, pk, object_name="Объект"):
        try:
            if isinstance(pk, str) and ("{{" in pk or "}}" in pk):
                return Response({"errors": f"Неверный ID {object_name.lower()}: {pk}"}, status=status.HTTP_400_BAD_REQUEST)
            pk = int(pk)
        except (ValueError, TypeError):
            return Response({"errors": f"Неверный формат ID {object_name.lower()}: {pk}"}, status=status.HTTP_400_BAD_REQUEST)
        obj = model.objects.filter(id=pk).first()
        if not obj:
            return Response({"errors": f"{object_name} не найден"}, status=status.HTTP_404_NOT_FOUND)
        return obj

    def destroy(self, request, *args, **kwargs):
        pk = kwargs.get('pk')
        obj = self.get_object_or_404_with_error(Recipe, pk, "Рецепт")
        if isinstance(obj, Response):
            return obj
        if obj.author != request.user:
            return Response({"errors": "Удалять рецепт может только автор."}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)

    @handle_api_errors
    def add_to(self, model, user, pk):
        """Добавление рецепта в избранное/список покупок с корректным статусом."""
        try:
            if isinstance(pk, str) and ('{{' in pk or '}}' in pk):
                return Response({"errors": f"Неверный ID рецепта: {pk}"}, status=status.HTTP_400_BAD_REQUEST)
            pk = int(pk)
            recipe = Recipe.objects.filter(id=pk).first()
            if not recipe:
                return Response({"errors": "Рецепт не найден"}, status=status.HTTP_404_NOT_FOUND)
            if model.objects.filter(user=user, recipe=recipe).exists():
                if model == Favorite:
                    return Response({"errors": "Рецепт уже в избранном"}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response({"errors": "Рецепт уже в списке покупок"}, status=status.HTTP_400_BAD_REQUEST)
            model.objects.create(user=user, recipe=recipe)
            serializer = RecipeShortSerializer(
                recipe, context={'request': self.request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ValueError as exc:
            return Response({"errors": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    @handle_api_errors
    def delete_from(self, model, user, pk):
        """Удаление рецепта из избранного/списка покупок с корректным статусом."""
        try:
            if isinstance(pk, str) and ('{{' in pk or '}}' in pk):
                return Response({"errors": f"Неверный ID рецепта: {pk}"}, status=status.HTTP_400_BAD_REQUEST)
            pk = int(pk)
            recipe = Recipe.objects.filter(id=pk).first()
            if not recipe:
                return Response({"errors": "Рецепт не найден"}, status=status.HTTP_404_NOT_FOUND)
            obj = model.objects.filter(user=user, recipe=recipe)
            if obj.exists():
                obj.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            if model == Favorite:
                return Response({"errors": "Рецепта нет в избранном"}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({"errors": "Рецепта нет в списке покупок"}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError as exc:
            return Response({"errors": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True, methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    @handle_api_errors
    def favorite(self, request, pk=None):
        """Добавить или удалить рецепт из избранного."""
        if request.method == 'POST':
            # Проверка на существование рецепта
            recipe = Recipe.objects.filter(id=pk).first()
            if not recipe:
                return Response(
                    {"errors": "Рецепт не найден"},
                    status=status.HTTP_404_NOT_FOUND
                )
            # Проверка на дублирование
            if Favorite.objects.filter(
                user=request.user, recipe=recipe
            ).exists():
                return Response(
                    {"errors": "Рецепт уже в избранном"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Favorite.objects.create(user=request.user, recipe=recipe)
            serializer = RecipeShortSerializer(
                recipe, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        # DELETE
        recipe = Recipe.objects.filter(id=pk).first()
        if not recipe:
            return Response(
                {"errors": "Рецепт не найден"},
                status=status.HTTP_404_NOT_FOUND
            )
        obj = Favorite.objects.filter(user=request.user, recipe=recipe)
        if not obj.exists():
            return Response(
                {"errors": "Рецепта нет в избранном"},
                status=status.HTTP_400_BAD_REQUEST
            )
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True, methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    @handle_api_errors
    def shopping_cart(self, request, pk=None):
        """Добавить или удалить рецепт из списка покупок."""
        if request.method == 'POST':
            recipe = Recipe.objects.filter(id=pk).first()
            if not recipe:
                return Response(
                    {"errors": "Рецепт не найден"},
                    status=status.HTTP_404_NOT_FOUND
                )
            if ShoppingCart.objects.filter(
                user=request.user, recipe=recipe
            ).exists():
                return Response(
                    {"errors": "Рецепт уже в списке покупок"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            ShoppingCart.objects.create(user=request.user, recipe=recipe)
            serializer = RecipeShortSerializer(
                recipe, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        recipe = Recipe.objects.filter(id=pk).first()
        if not recipe:
            return Response(
                {"errors": "Рецепт не найден"},
                status=status.HTTP_404_NOT_FOUND
            )
        obj = ShoppingCart.objects.filter(user=request.user, recipe=recipe)
        if not obj.exists():
            return Response(
                {"errors": "Рецепта нет в списке покупок"},
                status=status.HTTP_400_BAD_REQUEST
            )
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True, methods=['get'],
        url_path='get-link',
        permission_classes=[AllowAny]
    )
    def get_link(self, request, pk=None):
        """Получить короткую ссылку на рецепт."""
        recipe = self.get_object_or_404_with_error(Recipe, pk, "Рецепт")
        if isinstance(recipe, Response):
            return recipe
        short_link = request.build_absolute_uri(f"/recipes/{pk}/")
        return Response({"short-link": short_link})

    @action(detail=False, permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        """Скачать список покупок пользователя."""
        user = request.user
        if not user.shopping_cart.exists():
            return Response(
                {"errors": "Список покупок пуст"},
                status=status.HTTP_400_BAD_REQUEST
            )
        ingredients = RecipeIngredient.objects.filter(
            recipe__shopping_cart__user=user
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(
            amount=Sum('amount')
        ).order_by('ingredient__name')
        shopping_list = "Список покупок:\n\n"
        for ingredient in ingredients:
            shopping_list += (
                f"{ingredient['ingredient__name']} "
                f"({ingredient['ingredient__measurement_unit']}) — "
                f"{ingredient['amount']}\n"
            )
        from datetime import datetime
        now = datetime.now()
        date_str = now.strftime("%d-%m-%Y %H:%M")
        shopping_list += f"\nСписок создан: {date_str}"
        return create_file_from_data(
            shopping_list,
            'shopping_list.txt',
            'text/plain'
        )

    def list(self, request, *args, **kwargs):
        """Получить список рецептов с фильтрацией и пагинацией."""
        queryset = self.filter_queryset(self.get_queryset())
        author = request.query_params.get('author')
        if author:
            queryset = queryset.filter(author__id=author)
        is_favorited = request.query_params.get('is_favorited')
        if is_favorited == '1':
            if request.user.is_authenticated:
                queryset = queryset.filter(favorites__user=request.user)
            else:
                queryset = queryset.none()
        is_in_shopping_cart = request.query_params.get('is_in_shopping_cart')
        if is_in_shopping_cart == '1':
            if request.user.is_authenticated:
                queryset = queryset.filter(shopping_cart__user=request.user)
            else:
                queryset = queryset.none()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """Создать новый рецепт."""
        serializer = self.get_serializer(
            data=request.data, context={'request': request}
        )
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
        except ValidationError as exc:
            return Response(
                {'errors': exc.detail},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as exc:
            return Response(
                {'errors': str(exc)},
                status=status.HTTP_400_BAD_REQUEST
            )
        data = RecipeListSerializer(
            serializer.instance, context={'request': request}
        ).data
        headers = self.get_success_headers(serializer.data)
        return Response(data, status=status.HTTP_201_CREATED, headers=headers)
