from django.contrib import admin

from recipes.models import (Recipe, Tag, Ingredient,
                            IngredientAmount, Favourite, ShoppingCart)


class IngredientAmountInstanceInline(admin.TabularInline):
    model = IngredientAmount
    extra = 1
    min_num = 1


@admin.register(Recipe)
class RecipesAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'author',
    )
    inlines = [IngredientAmountInstanceInline]
    list_filter = ('name', )


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'slug',)
    list_filter = ('name', 'slug',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', )
    list_filter = ('name', )


@admin.register(Favourite)
class FavouriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe',)
    list_filter = ('user', )


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe',)
    list_filter = ('user', )
