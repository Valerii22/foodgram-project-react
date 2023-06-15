from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.db.models import Sum
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import (viewsets, status)
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .serializers import (RecipeSerializer, TagSerializer,
                          SubscriptionSerializer, RecipeCreateUpdateSerializer,
                          ShortRecipeSerializer, IngredientSerializer)
from .permissions import IsAuthorOrAdminPermission
from .pagination import CustomPagination
from .filters import RecipeFilter
from users.models import User, Follow
from recipes.models import (RecipeIngredient,
                            Recipe, ShoppingCart,
                            Tag, Ingredient, Favourite)


class CurrentUserViewSet(UserViewSet):
    """Пользовательский вьюсет"""

    pagination_class = CustomPagination

    @action(
        methods=['get'], detail=False,
        serializer_class=SubscriptionSerializer,
        permission_classes=(IsAuthenticated, )
    )
    def subscriptions(self, request):
        subscriptions = User.objects.filter(
            following__user=request.user
        )
        paginated_subscriptions = self.paginate_queryset(
            subscriptions
        )
        serialized_subscriptions = SubscriptionSerializer(
            paginated_subscriptions,
            many=True, context={'request': request}
        ).data
        return self.get_paginated_response(serialized_subscriptions)

    @action(
        methods=['post', 'delete'], detail=True,
        serializer_class=SubscriptionSerializer,
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request, id=None):
        user = request.user
        author = get_object_or_404(User, pk=id)

        follow_search = Follow.objects.filter(user=user, author=author)

        if request.method == 'POST':
            if user == author:
                return Response({'detail': 'Подписаться на себя запрещено'},
                                status=status.HTTP_400_BAD_REQUEST)
            if follow_search.exists():
                return Response(
                    {'detail': 'Вы уже подписаны на этого пользователя'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Follow.objects.create(user=user, author=author)
            serializer = self.get_serializer(author)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if not follow_search.exists():
            return Response(
                {'detail': 'Вы не подписаны на этого пользователя'},
                status=status.HTTP_400_BAD_REQUEST
            )
        Follow.objects.filter(user=user, author=author).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.ModelViewSet):

    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(viewsets.ModelViewSet):

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)


class CreateDeliteMixin:

    @staticmethod
    def create_method(model, pk, request):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        if model.objects.filter(recipe=recipe, user=user).exists():
            return Response(
                {'errors': 'Уже добавлен'},
                status=status.HTTP_400_BAD_REQUEST
            )
        model.objects.create(user=user, recipe=recipe)
        serializer = ShortRecipeSerializer(
            instance=recipe, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @staticmethod
    def delete_method(model, pk, request):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        if not model.objects.filter(user=user, recipe=recipe).exists():
            return Response(
                {'errors': 'Уже удален'},
                status=status.HTTP_400_BAD_REQUEST
            )
        model.objects.filter(user=user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RecipeViewSet(viewsets.ModelViewSet, CreateDeliteMixin):
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrAdminPermission,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.action in ('create', 'partial_update'):
            return RecipeCreateUpdateSerializer

        return RecipeSerializer

    @action(
        detail=True,
        methods=('POST', 'DELETE'),
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        if request.method == 'POST':
            return self.create_method(Favourite, pk, request)
        return self.delete_method(Favourite, pk, request)

    @action(
        detail=True,
        methods=('POST', 'DELETE'),
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        if request.method == 'POST':
            return self.create_method(ShoppingCart, pk, request)
        return self.delete_method(ShoppingCart, pk, request)

    @action(detail=False, methods=['get'],
            permission_classes=(IsAuthenticated,))
    def download_shopping_cart(self, request, **kwargs):
        ingredients = (
            RecipeIngredient.objects
            .filter(recipe__shopping_recipe__user=request.user)
            .values('ingredient')
            .annotate(total_amount=Sum('amount'))
            .values_list('ingredient__name', 'total_amount',
                         'ingredient__measurement_unit')
        )
        file_list = []
        [file_list.append(
            '{} - {} {}.'.format(*ingredient)) for ingredient in ingredients]
        file = HttpResponse('Cписок покупок:\n' + '\n'.join(file_list),
                            content_type='text/plain')
        file['Content-Disposition'] = (f'attachment; filename={FILE_NAME}')
        return file
