from rest_framework import status


class AppException(Exception):
    def __init__(
        self, message, status_code=status.HTTP_400_BAD_REQUEST, code="APP_ERROR"
    ):
        self.message = message
        self.status_code = int(status_code)
        self.code = code
        super().__init__(message)
