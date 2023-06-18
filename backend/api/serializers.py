from django.db.transaction import atomic
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import SerializerMethodField
from rest_framework.serializers import ModelSerializer, PrimaryKeyRelatedField
from drf_extra_fields.fields import Base64ImageField

from recipes.models import (Favourite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from users.models import Follow, User


class CurrentUserSerializer(serializers.ModelSerializer):

    password = serializers.CharField(write_only=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'password', 'is_subscribed'
        )
        write_only_fields = ('password',)

    def get_is_subscribed(self, obj):
        """Статус подписки на автора."""
        user_id = self.context.get('request').user.id
        return Follow.objects.filter(
            author=obj.id, user=user_id).exists()

    def create(self, validated_data):
        """Создание нового пользователя."""
        user = User.objects.create(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
        )
        user.set_password(validated_data['password'])
        user.save()
        return user
      
      
class ShortRecipeSerializer(ModelSerializer):
    '''
    Дополнительный сериализатор для отображения рецептов
    в подписках, избранном и покупках
    '''

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscribeSerializer(CurrentUserSerializer):
    '''Сериализатор подписoк'''

    recipes_count = serializers.ReadOnlyField(source='author.recipes.count',
                                              read_only=True)
    recipes = ShortRecipeSerializer(many=True, read_only=True)
    is_subscribed = serializers.BooleanField(default=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name',
                  'last_name', 'recipes_count', 'recipes',
                  'is_subscribed')
        read_only_fields = ('email', 'username',
                            'first_name', 'last_name')


class TagSerializer(serializers.ModelSerializer):
    '''Сериализатор тегов'''

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    '''Сериализатор ингредиентов'''

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientRecipeCreationSerializer(ModelSerializer):
    '''Сериализатор для вывода ингредиента при создании рецепта'''

    id = PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount', 'name', 'measurement_unit')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['id'] = instance.ingredient.id
        return data


class RecipeGetSerializer(ModelSerializer):
    '''Сериализатор получения рецепта'''

    tags = TagSerializer(many=True, read_only=True)
    author = CurrentUserSerializer(read_only=True)
    ingredients = IngredientRecipeCreationSerializer(
        source='recipeingredient', many=True)
    image = Base64ImageField()
    is_favorited = SerializerMethodField(read_only=True)
    is_in_shopping_cart = SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart', 'name',
                  'image', 'text', 'cooking_time')

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


class RecipeCreateSerializer(ModelSerializer):
    '''Сериализатор создания рецепта'''

    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(),
                                              many=True)
    author = CurrentUserSerializer(read_only=True)
    ingredients = IngredientRecipeCreationSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients',
                  'name', 'image', 'text', 'cooking_time')

    def validate_tags(self, value):
        if not value:
            raise ValidationError('Добавьте тег.')
        return value

    def validate_ingredients(self, value):
        '''Валидатор ингредиентов'''
        ingredients = value
        if not ingredients:
            raise ValidationError({
                'ingredients': 'Добавьте хотя бы один ингредиент!'
            })
        ingredients_list = []
        for item in ingredients:
            if item['id'] in ingredients_list:
                raise ValidationError({
                    'ingredients': 'Ингредиенты не должны дублироваться!'
                })
            if int(item['amount']) <= 0:
                raise ValidationError({
                    'amount': 'Количество должно быть больше нуля!'
                })
            ingredients_list.append(item['id'])
        return value

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        return RecipeGetSerializer(instance,
                                   context=context).data

    def addon_for_create_update_methods(self, ingredients, tags, recipe):
        recipe.tags.set(tags)
        RecipeIngredient.objects.bulk_create([RecipeIngredient(
            recipe=recipe,
            ingredient=ingredient['id'],
            amount=ingredient['amount'],
        ) for ingredient in ingredients])
        return recipe

    @atomic
    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        self.addon_for_create_update_methods(ingredients, tags, recipe)
        return recipe

    @atomic
    def update(self, recipe, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe.tags.clear()
        recipe.ingredients.clear()
        self.addon_for_create_update_methods(ingredients, tags, recipe)
        return super().update(recipe, validated_data)
