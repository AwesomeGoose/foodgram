from django_filters.rest_framework import (
    BooleanFilter,
    CharFilter,
    FilterSet,
    ModelMultipleChoiceFilter,
)

from recipes.models import Recipe, Tag


class RecipeFilter(FilterSet):
    is_in_shopping_cart = BooleanFilter(method="get_shopping_cart")
    is_favorited = BooleanFilter(method="get_favorite")
    tags = ModelMultipleChoiceFilter(
        field_name="tags__slug",
        to_field_name="slug",
        queryset=Tag.objects.all()
    )

    def get_shopping_cart(self, queryset, _, value):
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(shopping_cart__user=user)
        return queryset

    def get_favorite(self, queryset, _, value):
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(favorites__user=user)
        return queryset

    class Meta:
        model = Recipe
        fields = ("author", "tags", "is_favorited", "is_in_shopping_cart")


class IngredientFilter(FilterSet):
    name = CharFilter(lookup_expr="istartswith", field_name="name")
