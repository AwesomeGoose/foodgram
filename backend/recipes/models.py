"""
Модели рецептов
"""
import random
import string

from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from backend.constants import (
    MAX_ING_NAME_LENGTH,
    MAX_MEASUREMENT_UNIT_LENGTH,
    MIN_COOKING_TIME,
    MIN_ING_AMOUNT,
    MAX_RECIPE_NAME_LENGTH,
    TAG_NAME_LENGTH,
    TAG_SLUG_LENGTH,
)

User = get_user_model()


class Tag(models.Model):
    """Модель для хранения тегов рецептов"""

    name = models.CharField(
        verbose_name=_("Название тега"),
        max_length=TAG_NAME_LENGTH,
        unique=True,
        help_text=_("Укажите уникальное название тега"),
    )
    slug = models.SlugField(
        verbose_name=_("Слаг тега"),
        max_length=TAG_SLUG_LENGTH,
        unique=True,
        help_text=_("Укажите уникальный идентификатор для тега (slug)"),
    )

    class Meta:
        verbose_name = _("Тег")
        verbose_name_plural = _("Теги")
        ordering = ["name"]
        indexes = [
            models.Index(fields=["name"], name="tag_name_idx"),
        ]

    def __str__(self) -> str:
        return f"Тег: {self.name}"


class Ingredient(models.Model):
    """Модель для хранения информации об ингредиентах"""

    name = models.CharField(
        verbose_name=_("Название ингредиента"),
        max_length=MAX_ING_NAME_LENGTH,
        help_text=_("Введите название ингредиента"),
    )
    measurement_unit = models.CharField(
        verbose_name=_("Единица измерения"),
        max_length=MAX_MEASUREMENT_UNIT_LENGTH,
        help_text=_("Введите единицу измерения, например, 'грамм' или 'мл'"),
    )

    class Meta:
        verbose_name = _("Ингредиент")
        verbose_name_plural = _("Ингредиенты")
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["name", "measurement_unit"],
                name="unique_ingredient_constraint",
            )
        ]
        indexes = [
            models.Index(fields=["name"], name="ingredient_name_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.measurement_unit})"


class Recipe(models.Model):
    """Модель для хранения рецептов пользователей"""

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="recipes",
        verbose_name=_("Автор рецепта"),
        help_text=_("Пользователь, который создал рецепт"),
    )
    name = models.CharField(
        max_length=MAX_RECIPE_NAME_LENGTH,
        verbose_name=_("Название рецепта"),
        help_text=_("Введите название рецепта"),
    )
    text = models.TextField(
        verbose_name=_("Описание рецепта"),
        help_text=_("Добавьте подробное описание приготовления"),
    )
    image = models.ImageField(
        upload_to="recipes/images",
        verbose_name=_("Изображение рецепта"),
        help_text=_("Загрузите изображение готового блюда"),
    )
    cooking_time = models.PositiveIntegerField(
        verbose_name=_("Время приготовления (мин)"),
        validators=[
            MinValueValidator(
                MIN_COOKING_TIME,
                _("Минимальное время приготовления должно быть не менее 1 минуты"),
            )
        ],
        help_text=_("Укажите время приготовления в минутах"),
    )
    ingredients = models.ManyToManyField(
        "Ingredient",
        through="RecipeIngredient",
        related_name="recipes",
        verbose_name=_("Ингредиенты"),
        help_text=_("Выберите ингредиенты для рецепта"),
    )
    tags = models.ManyToManyField(
        "Tag",
        verbose_name=_("Теги"),
        help_text=_("Выберите теги для классификации рецепта"),
    )
    short_code = models.CharField(
        max_length=10,
        unique=True,
        null=True,
        blank=True,
        verbose_name="Короткий код"
    )

    class Meta:
        verbose_name = _("Рецепт")
        verbose_name_plural = _("Рецепты")
        ordering = ["name"]
        indexes = [
            models.Index(fields=["name"], name="recipe_name_idx"),
        ]

    def generate_short_code(self):
        while True:
            code = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
            if not Recipe.objects.filter(short_code=code).exists():
                return code

    def save(self, *args, **kwargs):
        if not self.short_code:  # Генерируем код только при создании
            self.short_code = self.generate_short_code()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.name} by {self.author}"


class RecipeIngredient(models.Model):
    """Связь ингредиента с рецептом"""

    recipe = models.ForeignKey(
        "Recipe",
        on_delete=models.CASCADE,
        related_name="recipe_ingredients",
        verbose_name=_("Рецепт"),
        help_text=_("Рецепт, содержащий этот ингредиент"),
    )
    ingredient = models.ForeignKey(
        "Ingredient",
        on_delete=models.CASCADE,
        verbose_name=_("Ингредиент"),
        help_text=_("Ингредиент, используемый в рецепте"),
    )
    amount = models.PositiveIntegerField(
        verbose_name=_("Количество"),
        validators=[
            MinValueValidator(
                MIN_ING_AMOUNT, _("Минимальное количество должно быть больше 0")
            )
        ],
        help_text=_("Укажите количество ингредиента"),
    )

    class Meta:
        verbose_name = _("Ингредиент рецепта")
        verbose_name_plural = _("Ингредиенты рецепта")
        constraints = [
            models.UniqueConstraint(
                fields=["recipe", "ingredient"],
                name="unique_recipe_ingredient_constraint",
            )
        ]

    def __str__(self) -> str:
        return f"{self.ingredient.name} ({self.amount}) для {self.recipe.name}"


class FavoriteShoppingCartBaseModel(models.Model):
    """Абстрактная базовая модель для избранного и корзины"""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_("Пользователь"),
        help_text=_("Пользователь, связанный с этим объектом"),
    )
    recipe = models.ForeignKey(
        "recipes.Recipe",
        on_delete=models.CASCADE,
        verbose_name=_("Рецепт"),
        help_text=_("Рецепт, добавленный в избранное или корзину"),
    )

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["user", "recipe"], name="user_recipe_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.recipe.name} для {self.user.username}"


class Favorites(FavoriteShoppingCartBaseModel):
    """Модель для хранения избранных рецептов"""

    class Meta:
        verbose_name = _("Избранное")
        verbose_name_plural = _("Избранные")
        default_related_name = "favorites"
        constraints = [
            models.UniqueConstraint(
                fields=["recipe", "user"],
                name="unique_favorite_constraint",
            )
        ]

    def __str__(self) -> str:
        return f"Избранное: {self.recipe.name} у {self.user.username}"


class ShoppingCart(FavoriteShoppingCartBaseModel):
    """Модель для хранения рецептов в корзине"""

    class Meta:
        verbose_name = _("Корзина")
        verbose_name_plural = _("Корзины")
        default_related_name = "shopping_cart"
        constraints = [
            models.UniqueConstraint(
                fields=["recipe", "user"],
                name="unique_shopping_cart_constraint",
            )
        ]

    def __str__(self) -> str:
        return f"Корзина: {self.recipe.name} у {self.user.username}"
