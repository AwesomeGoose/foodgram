from django.shortcuts import get_object_or_404
from django.core.files.base import ContentFile
from rest_framework import mixins, viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated, SAFE_METHODS
from django_filters.rest_framework import DjangoFilterBackend
from djoser.serializers import SetPasswordSerializer
import base64

from users.models import Person
from recipes.models import (Tag, Recipe, Ingredient,
                            Favourite, ShoppingCart, Follow)
from .serializers import (RecipeListSerializer, TagSerializer,
                          IngredientSerializer, FavouriteSerializer,
                          ShoppingCartSerializer, RecipeWriteSerializer,
                          UserSerializer, FollowSerializer,
                          UserListSerializer)
from .permissions import IsOwnerOrAdminOrReadOnly, IsUserOrAdminOrReadOnly
from .filters import IngredientSearchFilter, RecipeFilter
from .paginations import ApiPagination
from .download import shopping_cart


class UserViewSet(viewsets.ModelViewSet):
    queryset = Person.objects.all()
    permission_classes = (IsUserOrAdminOrReadOnly,)
    pagination_class = ApiPagination

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return UserListSerializer
        return UserSerializer

    @action(detail=False,
            methods=['get'],
            permission_classes=[IsAuthenticated])
    def me(self, request):
        user = self.request.user
        serializer = UserListSerializer(user, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False,
            methods=['put', 'delete'],
            permission_classes=[IsAuthenticated],
            url_path='me/avatar')
    def avatar(self, request):
        user = self.request.user

        if request.method == 'PUT':
            avatar_data = request.data.get('avatar')
            if avatar_data is None:
                return Response({'error': 'No avatar image provided.'}, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                format, imgstr = avatar_data.split(';base64,')
                ext = format.split('/')[-1]
                imgdata = base64.b64decode(imgstr)
                user.avatar.save(f'avatar.{ext}', ContentFile(imgdata), save=True)
                avatar_url = user.avatar.url
                return Response({'avatar': avatar_url}, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        elif request.method == 'DELETE':
            if hasattr(user, 'avatar'):
                user.avatar.delete(save=False)
                user.avatar = None
                user.save()
                return Response({'message': 'Avatar deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
            else:
                return Response({'error': 'No avatar found.'}, status=status.HTTP_404_NOT_FOUND)

    @action(["post"],
            detail=False,
            permission_classes=[IsAuthenticated])
    def set_password(self, request, *args, **kwargs):
        serializer = SetPasswordSerializer(
            data=request.data,
            context={'request': request})
        if serializer.is_valid(raise_exception=True):
            self.request.user.set_password(serializer.data["new_password"])
            self.request.user.save()
            return Response('Пароль успешно изменён',
                            status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True,
            methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def subscribe(self, request, *args, **kwargs):
        author = get_object_or_404(Person, id=self.kwargs.get('pk'))
        subscriber = self.request.user
        if request.method == 'POST':
            serializer = FollowSerializer(
                data=request.data,
                context={'request': request, 'author': author})
            if serializer.is_valid(raise_exception=True):
                serializer.save(author=author, subscriber=subscriber)
                return Response({'Успешная подписка': serializer.data},
                                status=status.HTTP_201_CREATED)
            return Response({'errors': 'Объект не найден'},
                            status=status.HTTP_404_NOT_FOUND)
        if Follow.objects.filter(author=author, subscriber=subscriber).exists():
            Follow.objects.get(author=author).delete()
            return Response('Успешная отписка',
                            status=status.HTTP_204_NO_CONTENT)
        return Response({'errors': 'Объект не найден'},
                        status=status.HTTP_404_NOT_FOUND)

    @action(detail=False,
            methods=['get'],
            permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        follows = Follow.objects.filter(subscriber=self.request.user)
        pages = self.paginate_queryset(follows)
        serializer = FollowSerializer(pages,
                                      many=True,
                                      context={'request': request})
        return self.get_paginated_response(serializer.data)
    
    def me_avatar(self, request):
        user = self.request.user
        if user.avatar:
            with open(user.avatar.path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                return Response({'avatar': encoded_string})
        else:
            return Response({'avatar': None})


class TagViewSet(mixins.ListModelMixin,
                 mixins.RetrieveModelMixin,
                 viewsets.GenericViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)


class IngredientViewSet(mixins.ListModelMixin,
                        mixins.RetrieveModelMixin,
                        viewsets.GenericViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filter_backends = (IngredientSearchFilter,)
    search_fields = ('name',)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (IsOwnerOrAdminOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    pagination_class = ApiPagination
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeListSerializer
        return RecipeWriteSerializer

    @action(detail=True,
            methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def favourite(self, request, *args, **kwargs):
        recipe = get_object_or_404(Recipe, id=self.kwargs.get('pk'))
        user = self.request.user
        if request.method == 'POST':
            if Favourite.objects.filter(author=user,
                                        recipe=recipe).exists():
                return Response({'errors': 'Рецепт уже добавлен!'},
                                status=status.HTTP_400_BAD_REQUEST)
            serializer = FavouriteSerializer(data=request.data)
            if serializer.is_valid(raise_exception=True):
                serializer.save(author=user, recipe=recipe)
                return Response(serializer.data,
                                status=status.HTTP_201_CREATED)
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
        if not Favourite.objects.filter(author=user,
                                        recipe=recipe).exists():
            return Response({'errors': 'Объект не найден'},
                            status=status.HTTP_404_NOT_FOUND)
        Favourite.objects.get(recipe=recipe).delete()
        return Response('Рецепт успешно удалён из избранного.',
                        status=status.HTTP_204_NO_CONTENT)

    @action(detail=True,
            methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, **kwargs):
        recipe = get_object_or_404(Recipe, id=self.kwargs.get('pk'))
        user = self.request.user
        if request.method == 'POST':
            if ShoppingCart.objects.filter(author=user,
                                           recipe=recipe).exists():
                return Response({'errors': 'Рецепт уже добавлен!'},
                                status=status.HTTP_400_BAD_REQUEST)
            serializer = ShoppingCartSerializer(data=request.data)
            if serializer.is_valid(raise_exception=True):
                serializer.save(author=user, recipe=recipe)
                return Response(serializer.data,
                                status=status.HTTP_201_CREATED)
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
        if not ShoppingCart.objects.filter(author=user,
                                           recipe=recipe).exists():
            return Response({'errors': 'Объект не найден'},
                            status=status.HTTP_404_NOT_FOUND)
        ShoppingCart.objects.get(recipe=recipe).delete()
        return Response('Рецепт успешно удалён из списка покупок.',
                        status=status.HTTP_204_NO_CONTENT)

    @action(detail=False,
            methods=['get'],
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        author = Person.objects.get(id=self.request.user.pk)
        if author.shopping_cart.exists():
            return shopping_cart(self, request, author)
        return Response('Список покупок пуст.',
                        status=status.HTTP_404_NOT_FOUND)
