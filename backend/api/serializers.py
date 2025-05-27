from django.core.validators import RegexValidator
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField

from recipes.models import (Ingredient, Tag, Recipe, RecipeIngredient,
                           Favorite, ShoppingCart)
from users.models import User, Follow
from .constants import (
    MIN_INGREDIENT_AMOUNT,
    MIN_COOKING_TIME,
    MAX_LENGTH_USERNAME,
    MAX_LENGTH_EMAIL,
    MAX_LENGTH_FIRST_NAME,
    MAX_LENGTH_LAST_NAME,
    ERROR_MIN_INGREDIENT_AMOUNT,
    ERROR_INGREDIENT_NOT_EXISTS,
    ERROR_USERNAME_REGEX,
    ERROR_USERNAME_EXISTS,
    ERROR_EMAIL_EXISTS,
)


def validate_username_field(value):
    """Общий валидатор для username."""
    import re
    if len(value) > MAX_LENGTH_USERNAME:
        raise serializers.ValidationError(
            f'Имя пользователя не может быть длиннее {MAX_LENGTH_USERNAME} символов.'
        )
    if value.lower() == 'me':
        raise serializers.ValidationError(
            'Имя пользователя "me" запрещено.'
        )
    if not re.match(r'^[\w.@+-]+$', value):
        raise serializers.ValidationError(ERROR_USERNAME_REGEX)
    return value


class CustomUserCreateSerializer(UserCreateSerializer):
    """Сериализатор для создания пользователя (только для регистрации)."""
    
    avatar = Base64ImageField(required=False, allow_null=True)
    username = serializers.CharField(
        max_length=MAX_LENGTH_USERNAME,
        validators=[
            RegexValidator(
                regex=r'^[\w.@+-]+$',
                message=ERROR_USERNAME_REGEX,
            ),
            UniqueValidator(
                queryset=User.objects.all(),
                message=ERROR_USERNAME_EXISTS
            ),
        ],
    )
    email = serializers.EmailField(
        max_length=MAX_LENGTH_EMAIL,
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message=ERROR_EMAIL_EXISTS
            )
        ],
    )
    first_name = serializers.CharField(max_length=MAX_LENGTH_FIRST_NAME)
    last_name = serializers.CharField(max_length=MAX_LENGTH_LAST_NAME)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
            'avatar',
        )
        extra_kwargs = {'password': {'write_only': True}}

    def validate_username(self, value):
        """Валидация username с использованием общего валидатора."""
        return validate_username_field(value)

    def create(self, validated_data):
        """Создание пользователя с поддержкой аватара."""
        avatar = validated_data.pop('avatar', None)
        user = super().create(validated_data)
        if avatar:
            user.avatar = avatar
            user.save()
        return user


class CustomUserSerializer(UserSerializer):
    """Сериализатор для пользователя (вывод)."""

    avatar = Base64ImageField(required=False, allow_null=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'avatar',
            'is_subscribed',
        )

    def get_is_subscribed(self, obj):
        """Возвращает статус подписки (True/False)."""
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return obj.following.filter(user=request.user).exists()


class SubscriptionSerializer(CustomUserSerializer):
    """Сериализатор для подписок на авторов."""
    
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    
    class Meta(CustomUserSerializer.Meta):
        fields = CustomUserSerializer.Meta.fields + ('recipes', 'recipes_count')
    
    def get_recipes(self, obj):
        """Получить рецепты автора."""
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit') if request else None
        recipes = obj.recipes.all()
        
        if recipes_limit:
            try:
                recipes = recipes[:int(recipes_limit)]
            except (ValueError, TypeError):
                pass
        
        serializer = RecipeShortSerializer(
            recipes, many=True, context=self.context
        )
        return serializer.data
        
    def get_recipes_count(self, obj):
        """Получить количество рецептов автора."""
        return obj.recipes.count()


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тегов."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов в рецепте."""

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')
        read_only_fields = ('id', 'name', 'measurement_unit')


class AddIngredientSerializer(serializers.Serializer):
    """Сериализатор для добавления ингредиентов при создании рецепта."""
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(
        min_value=MIN_INGREDIENT_AMOUNT,
        error_messages={
            'min_value': ERROR_MIN_INGREDIENT_AMOUNT
        }
    )


class RecipeShortSerializer(serializers.ModelSerializer):
    """Сериализатор для краткого представления рецепта."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')

class RecipeListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка рецептов."""
    
    author = CustomUserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        source='recipeingredient_set',
        many=True,
        read_only=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def get_is_favorited(self, obj):
        """Метод для получения статуса избранного."""
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return obj.favorites.filter(user=request.user).exists()

    def get_is_in_shopping_cart(self, obj):
        """Метод для получения статуса списка покупок."""
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return obj.shopping_cart.filter(user=request.user).exists()


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и обновления рецепта."""
    
    tags = TagSerializer(many=True, read_only=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = AddIngredientSerializer(many=True, write_only=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def validate(self, data):
        ingredients = data.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError(
                {'ingredients': ['Добавьте минимум один ингредиент!']}
            )
        ingredient_ids = [ingredient.get('id') for ingredient in ingredients]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                {'ingredients': ['Ингредиенты не могут повторяться!']}
            )
        tags = data.get('tags', [])
        if tags and len(tags) != len(set(tags)):
            raise serializers.ValidationError(
                {'tags': ['Теги не могут повторяться!']}
            )
        cooking_time = data.get('cooking_time')
        if cooking_time is None or int(cooking_time) < MIN_COOKING_TIME:
            raise serializers.ValidationError(
                {'cooking_time': ['Время приготовления должно быть не менее 1 минуты!']}
            )
        image = data.get('image')
        if not image:
            raise serializers.ValidationError(
                {'image': ['Загрузите изображение рецепта!']}
            )
        return data

    def _save_ingredients(self, recipe, ingredients_data):
        """Общий метод для сохранения ингредиентов."""
        recipe_ingredients = [
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient['id'],
                amount=ingredient['amount']
            )
            for ingredient in ingredients_data
        ]
        RecipeIngredient.objects.bulk_create(recipe_ingredients)

    def create(self, validated_data):
        tags = validated_data.pop('tags', [])
        ingredients_data = validated_data.pop('ingredients')
        request = self.context.get('request')
        author = request.user if request and request.user.is_authenticated else None
        recipe = Recipe.objects.create(author=author, **validated_data)
        if tags:
            recipe.tags.set(tags)
        self._save_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        ingredients_data = validated_data.pop('ingredients')
        if tags is not None:
            instance.tags.set(tags)
        instance.recipeingredient_set.all().delete()
        self._save_ingredients(instance, ingredients_data)
        return super().update(instance, validated_data)


class UserRegistrationResponseSerializer(serializers.ModelSerializer):
    """Сериализатор для ответа при регистрации пользователя."""
    
    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
        )
