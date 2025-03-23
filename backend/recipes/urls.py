from django.urls import path

from api.views import redirect_by_short_code

app_name = "recipes"

urlpatterns = [
    path('recipes/short/<str:short_code>/',
         redirect_by_short_code, name='short_link'),
]
