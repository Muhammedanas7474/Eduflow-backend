from rest_framework.views import exception_handler
from rest_framework.response import Response

from apps.common.exceptions import AppException


def custom_exception_handler(exc, context):
    # Handle AppException
    if isinstance(exc, AppException):
        return Response(
            {
                "success": False,
                "message": exc.message,
                "data": None
            },
            status=exc.status_code
        )

    # Default DRF exceptions
    response = exception_handler(exc, context)
    return response
