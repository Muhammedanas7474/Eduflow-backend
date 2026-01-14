# apps/common/exception_handler.py
from rest_framework.response import Response
from rest_framework.views import exception_handler
from apps.common.exceptions import AppException

def custom_exception_handler(exc, context):
    if isinstance(exc, AppException):
        return Response(
            {
                "success": False,
                "message": exc.message,
                "data": None
            },
            status=int(exc.status_code)  
        )

    response = exception_handler(exc, context)

    if response is not None:
        return Response(
            {
                "success": False,
                "message": response.data,
                "data": None
            },
            status=int(response.status_code)
        )

    return response
