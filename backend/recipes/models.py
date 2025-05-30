"""Модели для приложения recipes."""
from django.db import models
from django.core.validators import MinValueValidator

from users.models import User
from .constants import (
    MAX_LENGTH_INGREDIENT_NAME,
    MAX_LENGTH_INGREDIENT_MEASUREMENT_UNIT,
    MAX_LENGTH_TAG_NAME,
    MAX_LENGTH_TAG_COLOR,
    MAX_LENGTH_TAG_SLUG,
    MAX_LENGTH_RECIPE_NAME,
    MIN_COOKING_TIME,
    MIN_INGREDIENT_AMOUNT,
)


class Ingredient(models.Model):
    """Модель ингредиента."""

    name = models.CharField(
        'Название',
        max_length=MAX_LENGTH_INGREDIENT_NAME,
    )
    measurement_unit = models.CharField(
        'Единица измерения',
        max_length=MAX_LENGTH_INGREDIENT_MEASUREMENT_UNIT,
    )

    class Meta:
        """Метаданные модели Ingredient."""

        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ['name']

    def __str__(self):
        """Строковое представление модели."""
        return self.name


class Tag(models.Model):
    """Модель тега."""
    
    name = models.CharField(
        'Название',
        max_length=MAX_LENGTH_TAG_NAME,
        unique=True,
    )
    color = models.CharField(
        'Цвет',
        max_length=MAX_LENGTH_TAG_COLOR,
        unique=True,
    )
    slug = models.SlugField(
        'Слаг',        max_length=MAX_LENGTH_TAG_SLUG,
        unique=True,
    )

    class Meta:
        """Метаданные модели Tag."""

        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ['name']

    def __str__(self):
        """Строковое представление модели."""
        return self.name


class Recipe(models.Model):
    """Модель рецепта."""
    
    name = models.CharField(
        'Название',
        max_length=MAX_LENGTH_RECIPE_NAME,
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор публикации',
    )
    image = models.ImageField(
        'Картинка',
        upload_to='recipes/',
    )
    text = models.TextField(
        'Текстовое описание',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Ингредиенты',
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги',
    )
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления (в минутах)',
        validators=[MinValueValidator(MIN_COOKING_TIME)]
    )
    pub_date = models.DateTimeField(
        'Дата публикации',        auto_now_add=True,
        db_index=True,
    )

    class Meta:
        """Метаданные модели Recipe."""

        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ['-pub_date']

    def __str__(self):
        """Строковое представление модели."""
        return self.name


class RecipeIngredient(models.Model):
    """Связь между рецептом и ингредиентом с указанием количества."""
    
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )
    ingredient = models.ForeignKey(
        Ingredient,        on_delete=models.CASCADE,
        verbose_name='Ингредиент',
    )
    amount = models.PositiveSmallIntegerField(
        'Количество',
        validators=[MinValueValidator(MIN_INGREDIENT_AMOUNT)]
    )

    class Meta:
        """Метаданные модели RecipeIngredient."""

        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецепте'
        ordering = ['recipe']
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient'
            )
        ]

    def __str__(self):
        """Строковое представление модели."""
        return f'{self.ingredient.name} в {self.recipe.name}'


class Favorite(models.Model):
    """Модель избранного."""
    
    user = models.ForeignKey(        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Рецепт',
    )

    class Meta:
        """Метаданные модели Favorite."""

        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite'
            )
        ]

    def __str__(self):
        """Строковое представление модели."""
        return f'{self.user.username} добавил {self.recipe.name} в избранное'


class ShoppingCart(models.Model):
    """Модель корзины покупок."""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Рецепт',
    )

    class Meta:
        """Метаданные модели ShoppingCart."""

        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_shopping_cart'
            )
        ]

    def __str__(self):
        """Строковое представление модели."""
        return f'{self.user.username} добавил {self.recipe.name} в корзину'