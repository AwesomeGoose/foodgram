from django_filters.rest_framework import FilterSet, filters
from rest_framework.filters import SearchFilter

from recipes.models import Recipe, User, Tag


class IngredientSearchFilter(SearchFilter):
    search_param = 'name'


class RecipeFilter(FilterSet):
    author = filters.ModelChoiceFilter(
        queryset=User.objects.all())
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )
    is_in_shopping_cart = filters.NumberFilter(
        method='filter_is_in_shopping_cart')
    is_favourited = filters.NumberFilter(
        method='filter_is_favourited')

    class Meta:
        model = Recipe
        fields = ('tags', 'author', 'is_favourited', 'is_in_shopping_cart')

    def filter_is_favourited(self, queryset, name, value):
        if self.request.user.is_authenticated and value:
            return queryset.filter(favourite__author=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if self.request.user.is_authenticated and value:
            return queryset.filter(shoppingcart__author=self.request.user)
        return queryset
