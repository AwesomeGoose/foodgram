from django.db import transaction
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueTogetherValidator

from users.models import Subscriptions
from api.fields import Base64ImageField
from recipes.models import (Ingredient, Recipe, RecipeIngredient,
                            Tag, Favorites, ShoppingCart)

User = get_user_model()


class FavoritesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorites
        fields = ("recipe", "user")
        validators = [
            UniqueTogetherValidator(
                queryset=Favorites.objects.all(),
                fields=("recipe", "user"),
                message="Вы уже добавили этот рецепт в избранное.",
            )
        ]


class ShoppingCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingCart
        fields = ("recipe", "user")
        validators = [
            UniqueTogetherValidator(
                queryset=ShoppingCart.objects.all(),
                fields=("recipe", "user"),
                message="Вы уже добавили этот рецепт в корзину.",
            )
        ]


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "is_subscribed",
            "avatar",
        )

    def get_is_subscribed(self, obj) -> bool:
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return Subscriptions.objects.filter(user=request.user, author=obj).exists()


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = ("avatar",)

    def validate(self, value):
        if not value:
            raise ValidationError("Аватар обязателен для обновления.")
        return value


class SubscribeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscriptions
        fields = ("user", "author")
        validators = [
            UniqueTogetherValidator(
                queryset=Subscriptions.objects.all(),
                fields=("user", "author"),
                message="Вы уже подписаны на этого автора.",
            )
        ]

    def validate(self, data) -> dict:
        if data["user"] == data["author"]:
            raise serializers.ValidationError(
                "Подписка на себя запрещена"
            )
        return data

    def to_representation(self, instance):
        context = self.context
        return SubscriptionsSerializer(instance.author, context=context).data


class SubscriptionsSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "is_subscribed",
            "recipes",
            "recipes_count",
            "avatar",
        )

    def get_recipes(self, obj):
        request = self.context.get("request")
        recipes_limit = request.query_params.get("recipes_limit")

        recipes = obj.recipes.all()
        if recipes_limit and recipes_limit.isdigit():
            recipes = recipes[: int(recipes_limit)]

        return ShortRecipesSerializer(recipes, many=True, context=self.context).data

    @staticmethod
    def get_recipes_count(obj) -> int:
        return obj.recipes.count()


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = "__all__"


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = "__all__"


class RecipeIngredientWriteSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())

    class Meta:
        model = RecipeIngredient
        fields = ("id", "amount")


class RecipeIngredientReadSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source="ingredient.id")
    name = serializers.ReadOnlyField(source="ingredient.name")
    measurement_unit = serializers.ReadOnlyField(source="ingredient.measurement_unit")

    class Meta:
        model = RecipeIngredient
        fields = ("id", "name", "measurement_unit", "amount")


class RecipeReadSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer()
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField(default=False)
    is_in_shopping_cart = serializers.SerializerMethodField(default=False)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def get_ingredients(self, obj):
        ingredients = obj.recipe_ingredients.select_related('ingredient')
        return [
            {
                'id': ing.ingredient.id,
                'name': ing.ingredient.name,
                'measurement_unit': ing.ingredient.measurement_unit,
                'amount': ing.amount
            }
            for ing in ingredients
        ]

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        return (
                user.is_authenticated
                and obj.favorites.filter(user=user).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        return (
                user.is_authenticated
                and obj.shopping_cart.filter(user=user).exists()
        )


class RecipeSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(many=True, queryset=Tag.objects.all())
    ingredients = RecipeIngredientWriteSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            "ingredients",
            "tags",
            "image",
            "name",
            "text",
            "cooking_time",
        )
        read_only_fields = ("author",)

    def validate(self, data):
        ingredients = data.get("ingredients")
        if not ingredients:
            raise serializers.ValidationError("Нужен хотя бы один ингредиент.")
        unique_ing = {ing["id"] for ing in ingredients}
        if len(ingredients) != len(unique_ing):
            raise serializers.ValidationError("Ингредиенты не должны повторяться")
        tags = data.get("tags")
        if not tags:
            raise serializers.ValidationError("Нужен хотя бы один тег.")
        unique_tags = set(tags)
        if len(tags) != len(unique_tags):
            raise serializers.ValidationError("Теги не должны повторяться.")
        return data

    def to_representation(self, instance):
        context = {"request": self.context.get("request")}
        serializer = RecipeReadSerializer(instance, context=context)
        return serializer.data

    def create_ingredient(self, recipe, ingredients):
        return RecipeIngredient.objects.bulk_create(
            RecipeIngredient(recipe=recipe, ingredient=ing["id"], amount=ing["amount"])
            for ing in ingredients
        )

    @transaction.atomic
    def create(self, validated_data):
        ingredients = validated_data.pop("ingredients")
        tags = validated_data.pop("tags")
        recipe = Recipe.objects.create(
            author=self.context.get("request").user, **validated_data
        )
        self.create_ingredient(recipe, ingredients)
        recipe.tags.set(tags)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients = validated_data.pop("ingredients")
        instance.ingredients.clear()
        self.create_ingredient(instance, ingredients)
        tags = validated_data.pop("tags")
        instance.tags.set(tags)
        return super().update(instance, validated_data)


class ShortRecipesSerializer(serializers.ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")
