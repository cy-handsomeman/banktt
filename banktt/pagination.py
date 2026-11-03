from rest_framework.pagination import PageNumberPagination


class StandardPagination(PageNumberPagination):
    """统一分页：默认 10 条/页，允许前端用 page_size 调整，最多 100 条"""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100
