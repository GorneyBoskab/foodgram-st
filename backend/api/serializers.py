"""Сериализаторы для API."""
import base64
import uuid

from django.core.files.base import ContentFile
from django.core.validators import RegexValidator
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from djoser.serializers import UserCreateSerializer, UserSerializer

from recipes.models import (Ingredient, Tag, Recipe, RecipeIngredient,
                           Favorite, ShoppingCart)
from users.models import User, Follow


class Base64ImageField(serializers.ImageField):
    """Кастомное поле для работы с изображениями в base64."""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            image_name = str(uuid.uuid4())
            data = ContentFile(
                base64.b64decode(imgstr),
                name=f'{image_name}.{ext}'
            )
        return super().to_internal_value(data)


class CustomUserCreateSerializer(UserCreateSerializer):
    """Сериализатор для создания пользователя (только для регистрации)."""
    avatar = Base64ImageField(required=False, allow_null=True)
    username = serializers.CharField(
        max_length=150,
        validators=[
            RegexValidator(
                regex=r'^[\w.@+-]+$',
                message=(
                    'Некорректный username. Разрешены буквы, цифры и ./@/+/-.',
                ),
            ),
            UniqueValidator(
                queryset=User.objects.all(),
                message=(
                    'Пользователь с таким username уже существует.'
                ),
            ),
        ],
    )
    email = serializers.EmailField(
        max_length=254,
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message='Пользователь с таким email уже существует.'
            )
        ],
    )
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)

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
        """Валидация username: длина, запрещённые значения."""
        if len(value) > 150:
            raise serializers.ValidationError(
                'Имя пользователя не может быть длиннее 150 символов.'
            )
        if value.lower() == 'me':
            raise serializers.ValidationError(
                'Имя пользователя "me" запрещено.'
            )
        return value

    def validate_email(self, value):
        """Валидация email: длина."""
        if len(value) > 254:
            raise serializers.ValidationError(
                'Email не может быть длиннее 254 символов.'
            )
        return value

    def validate_first_name(self, value):
        """Валидация first_name: длина."""
        if len(value) > 150:
            raise serializers.ValidationError(
                'Имя не может быть длиннее 150 символов.'
            )
        return value

    def validate_last_name(self, value):
        """Валидация last_name: длина."""
        if len(value) > 150:
            raise serializers.ValidationError(
                'Фамилия не может быть длиннее 150 символов.'
            )
        return value

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

    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        """Meta-класс для CustomUserSerializer."""

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

    def get_avatar(self, obj):
        """Возвращает абсолютный URL аватара или null."""
        request = self.context.get('request')
        if obj.avatar:
            url = obj.avatar.url if hasattr(obj.avatar, 'url') else obj.avatar
            if request:
                return request.build_absolute_uri(url)
            return url
        return None

    def get_is_subscribed(self, obj):
        """Возвращает статус подписки (True/False)."""
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return Follow.objects.filter(user=request.user, author=obj).exists()

    def to_representation(self, instance):
        """Гарантирует строгую структуру и значения по умолчанию."""
        data = super().to_representation(instance)
        # avatar: всегда абсолютный url или null
        if 'avatar' not in data or not data['avatar']:
            data['avatar'] = None
        # is_subscribed: всегда bool
        data['is_subscribed'] = bool(data.get('is_subscribed', False))
        # Все обязательные поля присутствуют
        for field in self.Meta.fields:
            if field not in data:
                data[field] = None
        return data


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
            except Exception:
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

    id = serializers.IntegerField()
    amount = serializers.IntegerField(
        min_value=1,
        error_messages={
            'min_value': 'Количество ингредиента должно быть не менее 1.'
        }
    )

    def validate_id(self, value):
        if not Ingredient.objects.filter(id=value).exists():
            raise serializers.ValidationError('Ингредиент с таким ID не существует.')
        return value


class RecipeShortSerializer(serializers.ModelSerializer):
    """Сериализатор для краткого представления рецепта."""
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')

    def get_image(self, obj):
        request = self.context.get('request')
        if obj.image:
            url = obj.image.url if hasattr(obj.image, 'url') else obj.image
            if request:
                return request.build_absolute_uri(url)
            return url
        return None

class RecipeListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка рецептов."""
    tags = TagSerializer(many=True, read_only=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        source='recipeingredient_set',
        many=True,
        read_only=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def get_image(self, obj):
        request = self.context.get('request')
        if obj.image:
            url = obj.image.url if hasattr(obj.image, 'url') else obj.image
            if request:
                return request.build_absolute_uri(url)
            return url
        return None

    def get_is_favorited(self, obj):
        """Метод для получения статуса избранного."""
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return Favorite.objects.filter(user=request.user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        """Метод для получения статуса списка покупок."""
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(user=request.user, recipe=obj).exists()

class RecipeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и обновления рецепта."""
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    author = CustomUserSerializer(read_only=True)
    ingredients = AddIngredientSerializer(many=True)
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
        tags = data.get('tags')
        if not tags:
            raise serializers.ValidationError({'tags': ['Добавьте минимум один тег!']})
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError({'tags': ['Теги не могут повторяться!']})
        cooking_time = data.get('cooking_time')
        if cooking_time is None or int(cooking_time) < 1:
            raise serializers.ValidationError(
                {'cooking_time': ['Время приготовления должно быть не менее 1 минуты!']}
            )
        image = data.get('image')
        if not image:
            raise serializers.ValidationError({'image': ['Загрузите изображение рецепта!']})
        return data

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        for ingredient in ingredients_data:
            ingredient_obj = Ingredient.objects.get(id=ingredient['id'])
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient_obj,
                amount=ingredient['amount']
            )
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        ingredients_data = validated_data.pop('ingredients', None)
        if tags is not None:
            instance.tags.set(tags)
        if ingredients_data is not None:
            instance.recipeingredient_set.all().delete()
            for ingredient in ingredients_data:
                ingredient_obj = Ingredient.objects.get(id=ingredient['id'])
                RecipeIngredient.objects.create(
                    recipe=instance,
                    ingredient=ingredient_obj,
                    amount=ingredient['amount']
                )
        return super().update(instance, validated_data)

class FollowSerializer(serializers.ModelSerializer):
    """Сериализатор для подписок."""

    id = serializers.ReadOnlyField(source='author.id')
    email = serializers.ReadOnlyField(source='author.email')
    username = serializers.ReadOnlyField(source='author.username')
    first_name = serializers.ReadOnlyField(source='author.first_name')
    last_name = serializers.ReadOnlyField(source='author.last_name')
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = Follow
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
        )

    def get_is_subscribed(self, obj):
        """Метод для получения статуса подписки."""
        return True

    def get_recipes(self, obj):
        """Метод для получения рецептов автора."""
        request = self.context.get('request')
        limit = request.query_params.get('recipes_limit')
        recipes = Recipe.objects.filter(author=obj.author)
        if limit:
            try:
                recipes = recipes[:int(limit)]
            except ValueError:
                pass
        serializer = RecipeShortSerializer(
            recipes, many=True, context=self.context
        )
        return serializer.data

    def get_recipes_count(self, obj):
        """Метод для получения количества рецептов автора."""
        return Recipe.objects.filter(author=obj.author).count()

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
