from django.db.models.aggregates import Sum
from django.http import HttpResponse

from api.serializers import RecipeIngredient


def download_shopping_cart(request):
    ingredients = RecipeIngredient.objects.filter(
        recipe__shopping_cart__user=request.user).values(
            'ingredient__name', 'ingredient__measurement_unit').annotate(
                amount=Sum('total_amount'))
    text = ''
    for ingredient in ingredients:
        text += (f'•  {ingredient["ingredient__name"]}'
                 f'({ingredient["ingredient__measurement_unit"]})'
                 f'— {ingredient["total_amount"]}\n')
    headers = {
        'Content-Disposition': 'attachment; filename=cart.txt'}
    return HttpResponse(
        text, content_type='text/plain; charset=UTF-8', headers=headers)
