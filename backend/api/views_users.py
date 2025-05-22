"""Представления для работы с пользователями через API."""
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import serializers

from users.models import User, Follow
from api.serializers import CustomUserCreateSerializer, CustomUserSerializer
from django.shortcuts import get_object_or_404
from api.utils import handle_api_errors
from api.exceptions import (
    CannotSubscribeToYourself, AlreadySubscribed, NotSubscribed
)


class UserViewSet(DjoserUserViewSet):
    """API представление для работы с пользователями."""

    queryset = User.objects.all()

    def get_permissions(self):
        """Возвращает соответствующие разрешения в зависимости от действия."""
        if self.action in [
            'me', 'set_password', 'subscribe', 'subscriptions', 'avatar'
        ]:
            return [IsAuthenticated()]
        return [AllowAny()]

    def get_serializer_class(self):
        """Возвращает сериализатор в зависимости от действия."""
        if self.action == 'create':
            return CustomUserCreateSerializer
        elif self.action in ['subscriptions', 'subscribe']:
            from api.serializers import SubscriptionSerializer
            return SubscriptionSerializer
        return CustomUserSerializer

    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        Возвращает данные текущего пользователя с корректным avatar.
        """
        serializer = self.get_serializer(
            request.user, context={'request': request}
        )
        data = serializer.data
        if 'avatar' not in data or data['avatar'] is None:
            data['avatar'] = None
        return Response(data)

    @action(detail=False, methods=['post'])
    def set_password(self, request):
        """Изменяет пароль пользователя."""
        if (
            'current_password' not in request.data or
            'new_password' not in request.data
        ):
            return Response(
                {"errors": "Необходимы current_password и new_password"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not self.request.user.check_password(
            request.data['current_password']
        ):
            return Response(
                {"errors": "Неверный пароль"},
                status=status.HTTP_400_BAD_REQUEST
            )

        self.request.user.set_password(request.data['new_password'])
        self.request.user.save()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'], url_path='subscribe')
    @handle_api_errors
    def subscribe(self, request, pk=None, id=None):
        """Создать/удалить подписку на автора."""
        if pk is None and id is not None:
            pk = id
        author = get_object_or_404(User, id=pk)
        user = request.user

        if request.method == 'POST':
            if user == author:
                raise CannotSubscribeToYourself()

            if Follow.objects.filter(user=user, author=author).exists():
                raise AlreadySubscribed()

            Follow.objects.create(user=user, author=author)
            from api.serializers import SubscriptionSerializer
            serializer = SubscriptionSerializer(
                author, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        subscription = Follow.objects.filter(user=user, author=author)
        if not subscription.exists():
            raise NotSubscribed()
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def subscriptions(self, request):
        """Возвращает список подписок пользователя."""
        user = request.user
        follows = Follow.objects.filter(user=user).select_related('author')
        authors = [follow.author for follow in follows]
        page = self.paginate_queryset(authors)
        from api.serializers import SubscriptionSerializer
        serializer_class = SubscriptionSerializer
        if page is not None:
            serializer = serializer_class(
                page, many=True, context={'request': request}
            )
            return self.get_paginated_response(serializer.data)
        serializer = serializer_class(
            authors, many=True, context={'request': request}
        )
        return Response(serializer.data)

    @action(
        detail=False, methods=['post', 'put', 'delete'],
        url_path='me/avatar',
        permission_classes=[IsAuthenticated]
    )
    def avatar(self, request):
        """Устанавливает или удаляет аватар пользователя."""
        if not request.user.is_authenticated:
            return Response(
                {"detail": "Учётные данные не были предоставлены."},
                status=status.HTTP_401_UNAUTHORIZED
            )
        if request.method == 'DELETE':
            request.user.avatar = None
            request.user.save(update_fields=['avatar'])
            return Response(status=status.HTTP_204_NO_CONTENT)
        avatar_data = request.data.get('avatar')
        if not avatar_data:
            return Response(
                {"errors": "Файл аватара не передан."},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer = self.get_serializer(
            request.user,
            data={'avatar': avatar_data},
            partial=True,
            context={'request': request}
        )
        try:
            serializer.is_valid(raise_exception=True)
            serializer.save()
        except serializers.ValidationError as exc:
            detail = exc.detail if isinstance(exc.detail, str) else exc.detail
            return Response(
                {"errors": detail},
                status=status.HTTP_400_BAD_REQUEST
            )
        user_data = CustomUserSerializer(
            request.user, context={'request': request}
        ).data
        return Response({"avatar": user_data["avatar"]}, status=status.HTTP_200_OK)

    def create(self, request):
        """Создает нового пользователя.

        Возвращает только поля, требуемые по спецификации регистрации.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        user = User.objects.get(id=serializer.data['id'])
        from api.serializers import UserRegistrationResponseSerializer
        data = UserRegistrationResponseSerializer(user).data
        return Response(data, status=status.HTTP_201_CREATED)
