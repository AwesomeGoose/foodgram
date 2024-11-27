from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator

from foodgram.constants import (MAX_LENGTH_TAG, MAX_LENGTH_INGREDIENT,
                                MAX_MEASUREMENT, MAX_RECIPE_NAME,
                                MINIMAL_VALUE)

User = get_user_model()


class Tag(models.Model):
    name = models.CharField(max_length=MAX_LENGTH_TAG,
                            verbose_name='Имя тега',
                            unique=True)
    slug = models.SlugField(max_length=MAX_LENGTH_TAG,
                            verbose_name='Идентификатор',
                            unique=True)

    class Meta:
        verbose_name = 'тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(max_length=MAX_LENGTH_INGREDIENT,
                            verbose_name='Имя ингредиента',
                            unique=True)
    measurement_unit = models.CharField(max_length=MAX_MEASUREMENT,
                                        verbose_name='Единицы измерения')

    class Meta:
        verbose_name = 'ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='recipe',
                               verbose_name='Автор')
    name = models.CharField(max_length=MAX_RECIPE_NAME,
                            verbose_name='Название рецепта')
    text = models.TextField(verbose_name='Описание рецепта')
    ingredients = models.ManyToManyField(Ingredient,
                                         through='RecipeIngredient',
                                         verbose_name='Ингредиенты')
    tags = models.ManyToManyField(Tag)
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время готовки',
        validators=[MinValueValidator(MINIMAL_VALUE,
                                      'Невозможно приготовить так быстро')])
    image = models.ImageField(
        verbose_name='Картинка рецепта',
        upload_to='media/',
        help_text='Добавьте изображение рецепта')
    pub_date = models.DateTimeField(verbose_name='Дата публикации',
                                    auto_now_add=True)

    class Meta:
        verbose_name = 'рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ['-id']
        constraints = [models.UniqueConstraint(
            fields=['name', 'author'],
            name='unique_recipe')]

    def __str__(self):
        return (f'Рецепт {self.name}')


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe,
                               on_delete=models.CASCADE,
                               verbose_name='Рецепт')
    ingredient = models.ForeignKey(Ingredient,
                                   on_delete=models.CASCADE,
                                   verbose_name='Ингредиент')
    amount = models.IntegerField(
        verbose_name='Количество ингредиента',
        validators=[MinValueValidator(MINIMAL_VALUE,
                                      'Нет блюд без ингредиентов')])

    class Meta:
        verbose_name = 'Ассоциативная таблица рецепт-ингредиент'
        verbose_name_plural = 'Ассоциативные таблицы рецепты-ингредиенты'
        constraints = [models.UniqueConstraint(
            fields=['recipe', 'ingredient'],
            name='unique_ingredient')]

    def __str__(self):
        return f'{self.recipe.name}: {self.ingredient.name}'


class ShoppingCart(models.Model):
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               verbose_name='Автор')
    recipe = models.ForeignKey(Recipe,
                               on_delete=models.CASCADE,
                               verbose_name='Рецепт')

    class Meta:
        verbose_name = 'список покупок'
        verbose_name_plural = 'Списки покупок'
    constraints = [models.UniqueConstraint(
        fields=['author', 'recipe'],
        name='unique_cart')]

    def __str__(self):
        return self.recipe


class Favourite(models.Model):
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               verbose_name='Автор')
    recipe = models.ForeignKey(Recipe,
                               on_delete=models.CASCADE,
                               verbose_name='Рецепт')

    class Meta:
        verbose_name = 'избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        constraints = [models.UniqueConstraint(
            fields=['author', 'recipe'],
            name='unique_favourite')]

    def __str__(self):
        return self.recipe


class Follow(models.Model):
    subscriber = models.ForeignKey(User, on_delete=models.CASCADE,
                                   related_name='follower',
                                   verbose_name='Подписчик')
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='followed_author',
                               verbose_name='Автор')

    class Meta:
        verbose_name = 'подписка'
        verbose_name_plural = 'Подписки'
        constraints = [models.UniqueConstraint(
            fields=['subscriber', 'author'],
            name='unique_follow')]

    def __str__(self):
        return f'{self.subscriber} подписан на {self.author}'
