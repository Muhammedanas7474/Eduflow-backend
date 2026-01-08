class AppException(Exception):
    def __init__(self, message, code="APP_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)
