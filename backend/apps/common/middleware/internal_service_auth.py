import os

from django.http import JsonResponse

INTERNAL_SERVICE_TOKEN = os.getenv("INTERNAL_SERVICE_TOKEN")


class InternalServiceAuthMiddleware:
    """
    Allows ONLY trusted internal services (AI service)
    to access /internal/* endpoints.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Protect ONLY internal routes
        if request.path.startswith("/internal/"):
            token = request.headers.get("X-Service-Token")

            if not token or token != INTERNAL_SERVICE_TOKEN:
                return JsonResponse(
                    {"detail": "Forbidden: internal service only"}, status=403
                )

        return self.get_response(request)
