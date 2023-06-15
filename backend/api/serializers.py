from django.conf import settings
from django.core import exceptions
from django.core.validators import MinValueValidator
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from drf_extra_fields.fields import Base64ImageField

from recipes.models import Recipe, Ingredient, Favourite, ShoppingCart
from recipes.models import Tag, IngredientAmount
from users.models import Follow, User


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class CurrentUserSerializer(serializers.ModelSerializer):
    "Пользовательский сериализатор"
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed')
        model = User

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Follow.objects.filter(user=user, author=obj.id).exists()


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор для подписок"""

    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count'
        )

    def get_recipes(self, obj):
        limit = self.context['request'].query_params.get(
            'recipes_limit', settings.COUNT_RECIPES
        )
        recipes = obj.recipe.all()[:int(limit)]
        return ShortRecipeSerializer(recipes, many=True).data

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return Follow.objects.filter(user=user, author=obj.id).exists()

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class SubscriptionCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания подписки на автора."""

    class Meta:
        model = Follow
        fields = '__all__'

        validators = [
            UniqueTogetherValidator(
                queryset=Follow.objects.all(),
                fields=('user', 'author'),
                message='Вы уже подписаны на этого пользователя.'
            )
        ]

    def validate(self, data):
        if data['user'] == data['author']:
            raise serializers.ValidationError(
                'Вы не можете подписаться на самого себя.'
            )
        return data


class RecipeIngredientsSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientAmount
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    author = CurrentUserSerializer(read_only=True)
    tags = TagSerializer(many=True)
    ingredients = RecipeIngredientsSerializer(
        source='anount_recipe',
        many=True,
        read_only=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    def get_is_favorited(self, obj):
        user = self.context['request'].user

        if user.is_anonymous:
            return False

        return Favourite.objects.filter(user=user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user

        if user.is_anonymous:
            return False

        return ShoppingCart.objects.filter(user=user, recipe=obj).exists()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'text',
            'author',
            'ingredients',
            'tags',
            'cooking_time',
            'image',
            'name',
            'is_in_shopping_cart',
            'is_favorited',
        )


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    author = CurrentUserSerializer(read_only=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    ingredients = RecipeIngredientsSerializer(
        many=True,
        source='IngredientAmount'
    )
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(
        validators=(
            MinValueValidator(
                1,
                message='Время приготовления должно быть 1 или более.'
            ),
        )
    )

    def validate_tags(self, value):
        if not value:
            raise exceptions.ValidationError(
                'Нужно добавить хотя бы один тег.'
            )

        return value

    def validate_ingredients(self, value):
        if not value:
            raise exceptions.ValidationError(
                'Нужно добавить хотя бы один ингредиент.'
            )

        ingredients = [item['id'] for item in value]
        for ingredient in ingredients:
            if ingredients.count(ingredient) > 1:
                raise exceptions.ValidationError(
                    'У рецепта не может быть два одинаковых ингредиента.'
                )

        return value

    @staticmethod
    def create_ingredients(recipe, ingredients):
        ingredient_liist = []
        for ingredient_data in ingredients:
            ingredient_liist.append(
                IngredientAmount(
                    ingredient_id=ingredient_data.pop('id'),
                    amount=ingredient_data.pop('amount'),
                    recipe=recipe,
                )
            )
        IngredientAmount.objects.bulk_create(ingredient_liist)

    def create(self, validated_data):
        request = self.context.get('request', None)
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(author=request.user, **validated_data)
        recipe.tags.set(tags)
        self.create_ingredients(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data):
        instance.tags.clear()
        IngredientAmount.objects.filter(recipe=instance).delete()
        instance.tags.set(validated_data.pop('tags'))
        ingredients = validated_data.pop('ingredients')
        self.create_ingredients(instance, ingredients)
        return super().update(instance, validated_data)

    class Meta:
        model = Recipe
        fields = ('author', 'ingredients', 'tags', 'cooking_time', 'image')


class ShortRecipeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
