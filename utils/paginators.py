from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from functools import partial

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'total_pages': self.page.paginator.num_pages,
            'current_page': self.page.number,
            'results': data
        })

class LargeResultsSetPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 500

# Partial pour créer des paginateurs custom
create_paginator = partial(
    type,
    'CustomPaginator',
    (PageNumberPagination,),
    {'page_size': 10, 'page_size_query_param': 'limit', 'max_page_size': 50}
)


# from rest_framework.pagination import PageNumberPagination
# from functools import partial

# # Partial pour créer des paginateurs
# CustomPagination = partial(
#     type,
#     'CustomPagination',
#     (PageNumberPagination,),
#     {'page_size': 20, 'page_size_query_param': 'page_size', 'max_page_size': 100}
# )

# LargeResultsSetPagination = CustomPagination(page_size=100)
# StandardResultsSetPagination = CustomPagination(page_size=20)