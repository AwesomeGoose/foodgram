from django.db.models import Sum
from datetime import date
from django.http import HttpResponse

from recipes.models import RecipeIngredient


def shopping_cart(self, request, author):
    sum_ingredients = RecipeIngredient.objects.filter(
        recipe__shopping_cart__author=author
    ).values(
        'ingredient__name', 'ingredient__measurement_unit'
    ).annotate(
        amounts=Sum('amount', distinct=True)).order_by('amounts')
    today = date.today().strftime("%d-%m")
    shopping_list = f'Список покупок на: {today}\n\n'
    for ingredient in sum_ingredients:
        shopping_list += (
            f'{ingredient["ingredient__name"]} - '
            f'{ingredient["amounts"]} '
            f'{ingredient["ingredient__measurement_unit"]}\n'
        )
    shopping_list += '\n\nFoodgram'
    filename = 'shopping_list.txt'
    response = HttpResponse(shopping_list, content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename={filename}'
    return response
