from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(
        self,
        data,
        summary=None,
    ):
        response_data = {
            "items": data,
            "pagination": {
                "page": self.page.number,
                "page_size": self.get_page_size(
                    self.request
                ),
                "total_items": self.page.paginator.count,
                "total_pages": self.page.paginator.num_pages,
                "has_next": self.page.has_next(),
                "has_previous": self.page.has_previous(),
            },
        }

        if summary is not None:
            response_data["summary"] = summary

        return Response(
            {
                "success": True,
                "message": "Data fetched successfully.",
                "data": response_data,
            }
        )