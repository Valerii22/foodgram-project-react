from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import UniqueConstraint

from users.models import User


class Tag(models.Model):
    '''Модель тегов'''

    name = models.CharField(verbose_name='Имя тега',
                            max_length=200,
                            unique=True)
    color = models.CharField(verbose_name='Цвет HEX-код',
                             max_length=7,
                             unique=True)
    slug = models.SlugField(verbose_name='Слаг',
                            max_length=200,
                            unique=True)

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    '''Модель ингредиента'''

    name = models.CharField(verbose_name='Название',
                            max_length=200)
    measurement_unit = models.CharField(verbose_name='Единица измерения',
                                        max_length=200)

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('pk',)

    def __str__(self):
        return self.name


class Recipe(models.Model):
    '''Модель рецепта'''

    author = models.ForeignKey(User,
                               verbose_name='Автор',
                               on_delete=models.CASCADE,
                               related_name='recipes',)
    name = models.CharField(verbose_name='Название',
                            max_length=200)
    image = models.ImageField(verbose_name='Фото',
                              upload_to='recipes/')
    text = models.TextField(verbose_name='Текст')
    ingredients = models.ManyToManyField(Ingredient,
                                         verbose_name='Ингредиенты',
                                         through='RecipeIngredient',
                                         related_name='recipes')
    tags = models.ManyToManyField(Tag,
                                  verbose_name='Тег',
                                  related_name='recipes',
                                  blank=False)
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления, мин',
        validators=[MinValueValidator(1, message='Минимальное значение - 1!')])
    date = models.DateTimeField(verbose_name='Дата публикации',
                                auto_now_add=True)

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-date',)

    def __str__(self):
        return str(self.name)


class RecipeIngredient(models.Model):
    '''Модель ингредиентов для рецепта'''

    recipe = models.ForeignKey(Recipe,
                               verbose_name='Рецепт',
                               on_delete=models.CASCADE,
                               related_name='recipeingredient')
    ingredient = models.ForeignKey(Ingredient,
                                   verbose_name='Ингредиент',
                                   on_delete=models.CASCADE,
                                   related_name='recipeingredient')
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество', validators=(MinValueValidator(1),))

    class Meta:
        verbose_name = 'Ингредиент для рецепта'
        verbose_name_plural = 'Ингредиенты для рецепта'
        constraints = (
            UniqueConstraint(fields=('recipe', 'ingredient'),
                             name='recipeingredient'),
        )

    def __str__(self):
        return f'{str(self.ingredient)} in {str(self.recipe)}-{self.amount}'


class Favourite(models.Model):
    '''Модель избранного'''

    user = models.ForeignKey(User,
                             verbose_name='Пользователь',
                             on_delete=models.CASCADE,
                             related_name='favourites')
    recipe = models.ForeignKey(Recipe,
                               verbose_name='Рецепт',
                               on_delete=models.CASCADE,
                               related_name='favourites')

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'
        constraints = (
            UniqueConstraint(fields=('user', 'recipe'),
                             name='unique_favourite'),
        )

    def __str__(self):
        return f'Добавлено в избранное {self.recipe}'


class ShoppingCart(models.Model):
    '''Модель списка покупок'''

    user = models.ForeignKey(User,
                             verbose_name='Пользователь',
                             on_delete=models.CASCADE,
                             related_name='shopping_cart')
    recipe = models.ForeignKey(Recipe,
                               verbose_name='Рецепт',
                               on_delete=models.CASCADE,
                               related_name='shopping_cart')

    class Meta:
        verbose_name = 'Покупка'
        verbose_name_plural = 'Покупки'
        constraints = (
            UniqueConstraint(fields=('user', 'recipe'),
                             name='unique_shopping_cart'),
        )

    def __str__(self):
        return f'Добавлено в корзину {self.recipe}'
