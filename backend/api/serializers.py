from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError
from rest_framework.fields import SerializerMethodField

from recipes.models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                            ShoppingCart, Tag)
from users.models import User


class UserCreateSerializer(UserCreateSerializer):
    """ Сериализатор создания пользователя """

    class Meta:
        model = User
        fields = (
            'email', 'username', 'first_name',
            'last_name', 'password')


class UserSerializer(UserSerializer):
    """ Сериализатор пользователя """
    is_subscribed = SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed',)

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if self.context.get('request').user.is_anonymous:
            return False
        return obj.following.filter(user=request.user).exists()


class SubscribeSerializer(UserSerializer):
    """ Сериализатор для получения подписок """
    recipes_count = SerializerMethodField()
    recipes = SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('recipes_count', 'recipes')
        read_only_fields = ('email', 'username', 'first_name', 'last_name')

    def validate(self, data):
        author_id = self.context.get(
            'request').parser_context.get('kwargs').get('id')
        author = get_object_or_404(User, id=author_id)
        user = self.context.get('request').user
        if user.follower.filter(author=author_id).exists():
            raise ValidationError(
                detail='Подписка уже существует',
                code=status.HTTP_400_BAD_REQUEST,
            )
        if user == author:
            raise ValidationError(
                detail='Нельзя подписаться на самого себя',
                code=status.HTTP_400_BAD_REQUEST,
            )
        return data

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        recipes = obj.recipes.all()
        if limit:
            recipes = recipes[: int(limit)]
        serializer = RecipeShortSerializer(recipes, many=True, read_only=True)
        return serializer.data


class TagsSerializer(serializers.ModelSerializer):
    """ Сериализатор просмотра тегов """

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientsSerializer(serializers.ModelSerializer):
    """ Сериализатор просмотра ингредиентов """

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit', )


class IngredientRecipeSerializer(serializers.ModelSerializer):
    """ Сериализатор связи ингредиентов и рецепта """
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all())
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount',)


class RecipeReadSerializer(serializers.ModelSerializer):
    """ Сериализатор просмотра рецепта """
    author = UserSerializer(read_only=True, many=False)
    ingredients = IngredientRecipeSerializer(
        many=True,
        source='ingredienttorecipe')
    tags = TagsSerializer(read_only=False, many=True)
    is_favorited = serializers.SerializerMethodField()
    image = Base64ImageField(max_length=None)
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart',
                  'name', 'image', 'text', 'cooking_time')

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return obj.favorites.filter(user=request.user).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return obj.shopping_list.filter(user=request.user).exists()


class RecipeShortSerializer(serializers.ModelSerializer):
    """ Сериализатор полей избранных рецептов и покупок """

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FavoriteSerializer(serializers.ModelSerializer):
    """  Сериализатор избранных рецептов """

    class Meta:
        model = Favorite
        fields = ('user', 'recipe',)

    def validate(self, data):
        user = data['user']
        if user.favorites.filter(recipe=data['recipe']).exists():
            raise serializers.ValidationError(
                'Рецепт уже добавлен в избранное.'
            )
        return data

    def to_representation(self, instance):
        return RecipeShortSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}
        ).data


class CreateRecipeSerializer(serializers.ModelSerializer):
    """ Сериализатор для создания рецепта """
    ingredients = IngredientRecipeSerializer(
        many=True,)
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
        error_messages={'does_not_exist': 'Указанного тега не существует'}
    )
    image = Base64ImageField(max_length=None)
    author = UserSerializer(read_only=True)
    cooking_time = serializers.IntegerField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'name', 'image', 'text', 'cooking_time',)

    def create(self, validated_data):
        request = self.context.get('request')
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(author=request.user, **validated_data)
        recipe.save()
        recipe.tags.set(tags)
        self.create_ingredients(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data):
        instance.tags.clear()
        IngredientRecipe.objects.filter(recipe=instance).delete()
        instance.save()
        instance.tags.set(validated_data.pop('tags'))
        ingredients = validated_data.pop('ingredients')
        self.create_ingredients(instance, ingredients)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return RecipeReadSerializer(instance, context={
            'request': self.context.get('request')
        }).data

    def validate_tags(self, tags):
        for tag in tags:
            if not Tag.objects.filter(id=tag.id).exists():
                raise serializers.ValidationError(
                    'Указанный тег отсутствует в справочнике')
        return tags

    def validate_cooking_time(self, cooking_time):
        if cooking_time < 1:
            raise serializers.ValidationError(
                'Время приготовления блюда не может быть меньше одной минуты')
        return cooking_time

    def validate_ingredients(self, ingredients):
        ingredients_list = []
        if not ingredients:
            raise serializers.ValidationError(
                'Ингредиенты отсутствуют')
        for ingredient in ingredients:
            if ingredient['id'] in ingredients_list:
                raise serializers.ValidationError(
                    'Ингредиенты неуникальны')
            ingredients_list.append(ingredient['id'])
            if int(ingredient.get('amount')) < 1:
                raise serializers.ValidationError(
                    'Количество ингредиентов должно быть больше 0')
        return ingredients

    @staticmethod
    def create_ingredients(recipe, ingredients):
        ingredient_liist = []
        for ingredient_data in ingredients:
            ingredient_liist.append(
                IngredientRecipe(
                    ingredient=ingredient_data.pop('id'),
                    amount=ingredient_data.pop('amount'),
                    recipe=recipe,
                )
            )
        IngredientRecipe.objects.bulk_create(ingredient_liist)


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор для списка покупок """

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe',)

    def to_representation(self, instance):
        return RecipeShortSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}
        ).data

    def validate(self, data):
        user = data['user']
        if user.shopping_list.filter(recipe=data['recipe']).exists():
            raise serializers.ValidationError(
                'Рецепт уже находится в корзине'
            )
        return data