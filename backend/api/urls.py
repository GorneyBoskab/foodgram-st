from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api.views import (IngredientViewSet, TagViewSet,
                     RecipeViewSet)
from api.views_users import UserViewSet


app_name = 'api'

router = DefaultRouter()
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('tags', TagViewSet, basename='tags')
router.register('recipes', RecipeViewSet, basename='recipes')
router.register('users', UserViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
