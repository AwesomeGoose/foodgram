from typing import Optional

from rest_framework.pagination import PageNumberPagination

from backend.settings import RECIPE_PAGE_SIZE


class RecipePagination(PageNumberPagination):
    page_size_query_param: str = "limit"
    page_size: Optional[int] = RECIPE_PAGE_SIZE
