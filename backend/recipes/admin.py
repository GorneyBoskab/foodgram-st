"""Административный интерфейс для приложения recipes."""
from django.contrib import admin

from .models import (
    Ingredient, Tag, Recipe, RecipeIngredient, Favorite, ShoppingCart
)
from .constants import ADMIN_MIN_NUM_INGREDIENTS, ADMIN_EXTRA_INGREDIENTS


class RecipeIngredientInline(admin.TabularInline):
    """Инлайн модель для ингредиентов в рецепте."""

    model = RecipeIngredient
    min_num = ADMIN_MIN_NUM_INGREDIENTS
    extra = ADMIN_EXTRA_INGREDIENTS


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Административный интерфейс для модели Ingredient."""

    list_display = ('name', 'measurement_unit')
    list_filter = ('name',)
    search_fields = ('name',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Административный интерфейс для модели Tag."""

    list_display = ('name', 'color', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Административный интерфейс для модели Recipe."""

    list_display = ('name', 'author', 'get_favorites_count')
    list_filter = ('author', 'name', 'tags')
    readonly_fields = ('get_favorites_count',)
    inlines = (RecipeIngredientInline,)

    def get_favorites_count(self, obj):
        """Получить количество добавлений рецепта в избранное."""
        return obj.favorites.count()

    get_favorites_count.short_description = 'Количество в избранном'


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Административный интерфейс для модели Favorite."""

    list_display = ('user', 'recipe')
    list_filter = ('user',)


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Административный интерфейс для модели ShoppingCart."""

    list_display = ('user', 'recipe')
    list_filter = ('user',)
