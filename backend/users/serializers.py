from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from users.models import Follow

User = get_user_model()

class UserCreateSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        max_length=254,
        required=True
    )
    username = serializers.CharField(
        max_length=150,
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
        max_length=150,
        required=True
    )
    last_name = serializers.CharField(
        max_length=150,
        required=True
    )
    password = serializers.CharField(
        write_only=True,
        required=True
    )

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name', 'password'
        )

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('Пользователь с таким username уже существует.')
        if len(value) > 150:
            raise serializers.ValidationError('Максимальная длина username — 150 символов.')
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Пользователь с таким email уже существует.')
        if len(value) > 254:
            raise serializers.ValidationError('Максимальная длина email — 254 символа.')
        return value

    def validate_first_name(self, value):
        if len(value) > 150:
            raise serializers.ValidationError('Максимальная длина first_name — 150 символов.')
        return value

    def validate_last_name(self, value):
        if len(value) > 150:
            raise serializers.ValidationError('Максимальная длина last_name — 150 символов.')
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['is_subscribed'] = False
        data['avatar'] = instance.avatar.url if instance.avatar else ""
        return data

class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name', 'is_subscribed', 'avatar'
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return Follow.objects.filter(user=request.user, author=obj).exists()

    def get_avatar(self, obj):
        return obj.avatar.url if obj.avatar else ""
