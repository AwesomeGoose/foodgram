from django.contrib import admin

from foodgram.constants import EXTRA
from .models import (Recipe, Ingredient, Tag,
                     Favourite, Follow,
                     ShoppingCart, RecipeIngredient)


class IngredientsInline(admin.TabularInline):
    model = RecipeIngredient
    extra = EXTRA


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'name', 'pub_date', 'in_favourite')
    search_fields = ('name',)
    list_filter = ('pub_date', 'author', 'name', 'tags')
    filter_horizontal = ('ingredients',)
    empty_value_display = '-empty-'
    inlines = [IngredientsInline]

    def in_favourite(self, obj):
        return obj.favourite.all().count()


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('subscriber', 'author')
    list_filter = ('author',)
    search_fields = ('subscriber',)
    empty_value_display = '-empty-'


@admin.register(Favourite)
class FavouriteAdmin(admin.ModelAdmin):
    list_display = ('author', 'recipe')
    list_filter = ('author',)
    search_fields = ('author',)
    empty_value_display = '-empty-'


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('author', 'recipe')
    list_filter = ('author',)
    search_fields = ('author',)
    empty_value_display = '-empty-'


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'ingredient')
    list_filter = ('recipe', 'ingredient')
    search_fields = ('name',)
    empty_value_display = '-empty-'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug')
    list_filter = ('name',)
    search_fields = ('name',)
    empty_value_display = '-empty-'


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    list_filter = ('name',)
    search_fields = ('name',)
    empty_value_display = '-empty-'
