"""Сериализаторы для приложения users."""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from users.models import Follow
from .constants import (
    MAX_LENGTH_EMAIL,
    MAX_LENGTH_USERNAME,
    MAX_LENGTH_FIRST_NAME,
    MAX_LENGTH_LAST_NAME,
)

User = get_user_model()


class UserCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания пользователя."""
    
    email = serializers.EmailField(
        max_length=MAX_LENGTH_EMAIL,
        required=True
    )
    username = serializers.CharField(
        max_length=MAX_LENGTH_USERNAME,
        required=True,
        validators=[
            RegexValidator(
                regex=r'^[\w.@+-]+$',
                message='Введите корректное имя пользователя. '
                        'Допустимы только буквы, цифры и @/./+/-/_'
            )
        ]
    )
    first_name = serializers.CharField(
        max_length=MAX_LENGTH_FIRST_NAME,
        required=True
    )
    last_name = serializers.CharField(
        max_length=MAX_LENGTH_LAST_NAME,
        required=True
    )
    password = serializers.CharField(
        write_only=True,        required=True
    )

    class Meta:
        """Метаданные сериализатора."""

        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name', 'password'
        )

    def validate_username(self, value):
        """Валидация username."""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('Пользователь с таким username уже существует.')
        if len(value) > MAX_LENGTH_USERNAME:
            raise serializers.ValidationError('Максимальная длина username — 150 символов.')
        return value

    def validate_email(self, value):
        """Валидация email."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Пользователь с таким email уже существует.')
        if len(value) > MAX_LENGTH_EMAIL:
            raise serializers.ValidationError('Максимальная длина email — 254 символа.')
        return value

    def validate_first_name(self, value):
        """Валидация first_name."""
        if len(value) > MAX_LENGTH_FIRST_NAME:
            raise serializers.ValidationError('Максимальная длина first_name — 150 символов.')
        return value

    def validate_last_name(self, value):
        """Валидация last_name."""
        if len(value) > MAX_LENGTH_LAST_NAME:
            raise serializers.ValidationError('Максимальная длина last_name — 150 символов.')
        return value

    def create(self, validated_data):
        """Создание пользователя."""
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def to_representation(self, instance):
        """Представление пользователя."""
        data = super().to_representation(instance)
        data['is_subscribed'] = False
        data['avatar'] = instance.avatar.url if instance.avatar else ""
        return data


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для пользователя."""
      is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        """Метаданные сериализатора."""

        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name', 'is_subscribed', 'avatar'
        )

    def get_is_subscribed(self, obj):
        """Получить статус подписки."""
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return Follow.objects.filter(user=request.user, author=obj).exists()

    def get_avatar(self, obj):
        """Получить аватар пользователя."""
        return obj.avatar.url if obj.avatar else ""
