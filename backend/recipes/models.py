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

    name = models.CharField(
        max_length=200,
        verbose_name='Название рецепта',
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата',
        help_text='Укажите дату публикции',
        auto_now_add=True)
    text = models.TextField(
        verbose_name='Описание рецепта',
        null=True,
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления, мин',
        validators=[MinValueValidator(1), ]
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipe'
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='список тэгов',
        related_name='recipe'
    )
    image = models.ImageField(upload_to='uploads/',)

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)

    def __str__(self):
        return self.name[:15]


class IngredientAmount(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingrediens',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='+',
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name="Количество"
    )

    class Meta:
        verbose_name = 'Ингредиенты в рецепте'
        verbose_name_plural = 'Ингредиенты в рецепте'
        constraints = [
            models.UniqueConstraint(fields=['recipe', 'ingredient'],
                                    name='unique_recipe_ingredient')
        ]

    def __str__(self):
        return f'{self.ingredient}: {self.amount}'


class Favourite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favourite'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favourite'
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


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='+',
    )

    class Meta:
        verbose_name = 'Корзина покупок'
        constraints = [
            models.UniqueConstraint(fields=['user', 'recipe'],
                                    name='unique_shopping_cart')
        ]

    def __str__(self):
        return f'{self.user} добавил "{self.recipe}" в Корзину покупок'
