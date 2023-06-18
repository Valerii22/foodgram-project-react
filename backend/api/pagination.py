from rest_framework.pagination import PageNumberPagination


class CustomPagination(PageNumberPagination):
    page_size = 9
    page_size_query_param = 'limit'
    
    
class CustomSubscribePagination(PageNumberPagination):
    page_size = 3
    page_size_query_param = 'limit'
