from typing import Optional, Type
from django.db.models import Model, Sum
from django.contrib.auth import get_user_model
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserViews

from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from api.filters import IngredientFilter, RecipeFilter
from api.permissions import IsAuthorPermission
from api.utils import pdf_shopping_cart
from api.paginations import RecipePagination
from api.serializers import (FavoritesSerializer,
                             ShoppingCartSerializer,
                             UserSerializer,
                             AvatarSerializer,
                             SubscribeSerializer,
                             SubscriptionsSerializer,
                             RecipeSerializer,
                             ShortRecipesSerializer,
                             TagSerializer,
                             IngredientSerializer)
from recipes.models import (
    Favorites,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)

from users.models import Subscriptions

User = get_user_model()


class UserViewSet(DjoserViews):
    serializer_class = UserSerializer
    pagination_class = RecipePagination

    def get_permissions(self) -> list:
        if self.action == "me":
            self.permission_classes = (IsAuthenticated,)
        return super().get_permissions()

    @action(
        methods=["put"],
        url_path="me/avatar",
        serializer_class=AvatarSerializer,
        permission_classes=(IsAuthenticated,),
        detail=False,
    )
    def avatar(self, request: HttpRequest) -> Response:
        serializer = self.get_serializer(request.user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        data = serializer.data
        return Response(data, status=status.HTTP_200_OK)

    @avatar.mapping.delete
    def delete_avatar(self, request: HttpRequest) -> Response:
        user = request.user
        if user.avatar:
            user.avatar.delete()
            user.avatar = None
            user.save(update_fields=["avatar"])
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=["post"],
        url_path=r"(?P<pk>\d+)/subscribe",
        serializer_class=SubscribeSerializer,
        permission_classes=(IsAuthenticated,),
        detail=False,
    )
    def subscribe(self,
                  request: HttpRequest,
                  pk: Optional[int] = None) -> Response:
        author = get_object_or_404(User, id=pk)
        serializer = SubscribeSerializer(
            data={"user": request.user.id, "author": author.id}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        response_serializer = SubscriptionsSerializer(
            author, context={"request": request}
        )
        return Response(response_serializer.data,
                        status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self,
                    request: HttpRequest,
                    pk: Optional[int] = None) -> Response:
        author = get_object_or_404(User, id=pk)
        subscription_deleted = Subscriptions.objects.filter(
            user=request.user, author=author
        ).delete()[0]
        if not subscription_deleted:
            return Response(
                {"detail": "Вы не были подписаны на этого автора"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            {"detail": "Подписка отменена"}, status=status.HTTP_204_NO_CONTENT
        )

    @action(
        detail=False,
        url_path="subscriptions",
        permission_classes=(IsAuthenticated,),
        serializer_class=SubscriptionsSerializer,
    )
    def subscriptions(self, request: HttpRequest) -> Response:
        user_subscriptions = self.paginate_queryset(
            User.objects.filter(subscriptions__user=request.user)
        )
        serializer = SubscriptionsSerializer(
            user_subscriptions, many=True, context={"request": request}
        )
        data = serializer.data
        return self.get_paginated_response(data)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = [IsAuthorPermission]
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter
    pagination_class = RecipePagination

    def create_obj(
            self,
            create_serializer: Type[serializers.Serializer],
            request: HttpRequest,
            pk: Optional[int],
    ) -> Response:
        recipe = get_object_or_404(Recipe, id=pk)
        serializer = create_serializer(
            data={"user": request.user.id, "recipe": recipe.id}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        response_serializer = ShortRecipesSerializer(recipe)
        data = response_serializer.data
        return Response(data, status=status.HTTP_201_CREATED)

    def delete_obj(
            self, model: Type[Model], request: HttpRequest, pk: Optional[int]
    ) -> Response:
        recipe = get_object_or_404(Recipe, id=pk)
        obj_deleted = model.objects.filter(user=request.user,
                                           recipe=recipe).delete()[0]
        if not obj_deleted:
            return Response(
                {"detail": "Вы не добавляли этот рецепт"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response({"detail": "Рецепт удален"},
                        status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=["post"],
        url_path=r"(?P<pk>\d+)/favorite",
        serializer_class=FavoritesSerializer,
        detail=False,
    )
    def favorite(self,
                 request: HttpRequest,
                 pk: Optional[int] = None) -> Response:
        return self.create_obj(self.serializer_class, request, pk)

    @favorite.mapping.delete
    def del_favorite(self,
                     request: HttpRequest,
                     pk: Optional[int] = None) -> Response:
        return self.delete_obj(Favorites, request, pk)

    @action(
        methods=["post"],
        url_path=r"(?P<pk>\d+)/shopping_cart",
        serializer_class=ShoppingCartSerializer,
        detail=False,
    )
    def shopping_cart(self,
                      request: HttpRequest,
                      pk: Optional[int] = None) -> Response:
        return self.create_obj(self.serializer_class, request, pk)

    @shopping_cart.mapping.delete
    def del_shopping_cart(
            self, request: HttpRequest, pk: Optional[int] = None
    ) -> Response:
        return self.delete_obj(ShoppingCart, request, pk)

    @action(detail=False, permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request: HttpRequest) -> HttpResponse:
        shopping_cart = (
            RecipeIngredient.objects.filter(
                recipe__shopping_cart__user=request.user)
            .values("ingredient__name", "ingredient__measurement_unit")
            .order_by("ingredient__name")
            .annotate(ingredient_value=Sum("amount"))
        )
        return pdf_shopping_cart(shopping_cart)

    @action(detail=True, url_path="get-link", permission_classes=[AllowAny])
    def short_link(self,
                   request: HttpRequest,
                   pk: Optional[int] = None) -> Response:
        recipe = get_object_or_404(Recipe, id=pk)
        if not recipe.short_code:
            recipe.short_code = recipe.generate_short_code()
            recipe.save()
        short_url = request.build_absolute_uri(
            f"/recipes/short/{recipe.short_code}/")
        return Response({"short-link": short_url}, status=status.HTTP_200_OK)


class TagsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilter


def redirect_by_short_code(_, short_code):
    recipe = get_object_or_404(Recipe, short_code=short_code)
    return HttpResponseRedirect(f"/recipes/{recipe.pk}/")
