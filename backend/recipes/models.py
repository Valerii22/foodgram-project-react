from django.db import models
from django.core.validators import MinValueValidator

from users.models import User


class Ingredient(models.Model):
    name = models.CharField(
        max_length=200,
        verbose_name='Название ингредиента',
    )
    measurement_unit = models.CharField(
        max_length=200,
        verbose_name='Единица измерения',
        default="кг"
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(
        max_length=200,
        verbose_name='Название тэга',
    )
    color = models.CharField(
        max_length=7,
        default="#ffffff",
    )
    slug = models.SlugField(
        max_length=200,
        verbose_name='Уникальное имя цвета',
        unique=True,
    )

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name[:15]


class Recipe(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               verbose_name='Автор публикации',
                               related_name='recipes')
    name = models.CharField('Название', max_length=200)
    image = models.ImageField('Картинка', )
    text = models.TextField('Текстовое описание', )
    ingredients = models.ManyToManyField(Ingredient,
                                         verbose_name='Ингредиенты',
                                         through='IngredientAmount')
    tags = models.ManyToManyField(Tag, verbose_name='Теги')
    cooking_time = models.PositiveIntegerField(
        verbose_name='Время приготовления в минутах',
        validators=[MinValueValidator(1)],)
    pub_date = models.DateTimeField('Дата публикации', auto_now_add=True,
                                    db_index=True)

    class Meta:
        ordering = ('-id', )
        verbose_name = 'Рецепт'
        constraints = [
            models.UniqueConstraint(
                fields=['author', 'name'],
                name='unique_author_name'
            )
        ]

    def __str__(self):
        return f'Рецепт {self.name}'


class IngredientAmount(models.Model):
    recipe = models.ForeignKey(Recipe, verbose_name='Рецепт',
                               related_name='amount',
                               on_delete=models.CASCADE)
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество ингредиента',
        validators=[MinValueValidator(1)])
    ingredient = models.ForeignKey(Ingredient, verbose_name='Ингридиент',
                                   related_name='amount',
                                   on_delete=models.CASCADE)

    class Meta:
        ordering = ('-id', )
        verbose_name = 'Количество ингредиента'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='recipes_ingredient_2',
            )
        ]


class ShoppingCart(models.Model):
    user = models.ForeignKey(User, verbose_name='Пользователь',
                             related_name='Shopping_cart',
                             on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, verbose_name='Список рецептов',
                               related_name='shopping_cart',
                               on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Добавление рецепта в список покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='shopping_user_recipe'
            )
        ]

    def __str__(self):
        return f'{self.user}, {self.recipe}'



class Favourite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites'
    )

    class Meta:
        verbose_name = 'Избранное'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique favourite'
            ),
        ]

    def __str__(self):
        return self.user.get_username()
