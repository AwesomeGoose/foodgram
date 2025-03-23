from django.contrib import admin
from .models import Tag, Ingredient, Recipe, RecipeIngredient


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 0
    fields = ("ingredient", "amount")
    autocomplete_fields = ("ingredient",)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    inlines = [RecipeIngredientInline]
    list_display = ("name", "author", "favorite_count")
    search_fields = ("name", "author__username", "author__email")
    list_filter = ("tags", "author")
    readonly_fields = ("favorite_count",)
    autocomplete_fields = ("author",)
    ordering = ("-id",)

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related(
            "favorites", "tags")

    @admin.display(description="В избранных")
    def favorite_count(self, obj):
        return obj.favorites.count()


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ("name", "measurement_unit")
    search_fields = ("name",)
    list_filter = ("measurement_unit",)
    ordering = ("name",)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name", "slug")
    ordering = ("name",)
