from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication


class CookieAuthentication(JWTAuthentication):
    def authenticate(self, request):
        header = self.get_header(request)

        raw_token = None
        if header is None:
            raw_token = request.COOKIES.get(
                settings.SIMPLE_JWT.get("AUTH_COOKIE", "access_token")
            )
        else:
            raw_token = self.get_raw_token(header)

        if raw_token is None:
            print("DEBUG: No token found in headers or cookies")
            return None

        try:
            validated_token = self.get_validated_token(raw_token)
            return self.get_user(validated_token), validated_token
        except Exception as e:
            print(f"DEBUG: Authentication Failed: {e}")
            raise
