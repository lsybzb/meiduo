from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):

    page_size = 2   # 每页数量
    page_size_query_param = 'page_size' # 每页数量查询参数名称
    max_page_size = 5  #  每页最大数量