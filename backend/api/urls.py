from django.urls import include, path
from rest_framework import routers

from .views import (RecipeViewSet,
                       TagViewSet,
                       IngredientViewSet, CurrentUserViewSet)

app_name = 'api'


router = routers.DefaultRouter()
router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('recipes', RecipeViewSet, basename='recipes')
router.register('users', CurrentUserViewSet, basename='users')


urlpatterns = [
        path('', include(router.urls)),
        path('auth/', include('djoser.urls.authtoken'))
    ]  
