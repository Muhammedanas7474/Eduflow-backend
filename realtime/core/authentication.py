import jwt
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from .middleware import WebSocketUser


class StatelessJWTAuthentication(BaseAuthentication):
    """
    DRF Authentication that validates JWTs without checking the database.
    Reuses WebSocketUser logic to create an ephemeral user object.
    """

    def authenticate(self, request):
        token = None
        auth_header = request.headers.get("Authorization")

        # Log to track request arrival
        print(f"DEBUG AUTH: Request path: {request.path}")

        if auth_header:
            try:
                # Expect "Bearer <token>"
                parts = auth_header.split()
                if len(parts) == 2 and parts[0].lower() == "bearer":
                    token = parts[1]
                    print("DEBUG AUTH: Token found in Header")
            except ValueError:
                pass

        # If no header, check cookie
        if not token:
            token = request.COOKIES.get("access_token")
            if token:
                print("DEBUG AUTH: Token found in Cookie")

        if not token:
            print("DEBUG AUTH: No token found")
            return None

        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])

            print(f"DEBUG AUTH: Token decoded. User ID: {payload.get('user_id')}")

            user = WebSocketUser(
                user_id=payload.get("user_id"),
                tenant_id=payload.get("tenant_id"),
                role=payload.get("role"),
                full_name=payload.get("full_name", ""),
            )

            return (user, token)

        except jwt.ExpiredSignatureError:
            print("DEBUG AUTH: Token expired")
            raise AuthenticationFailed("Token has expired")
        except jwt.InvalidTokenError as e:
            print(f"DEBUG AUTH: Invalid token: {str(e)}")
            raise AuthenticationFailed(f"Invalid token: {str(e)}")
        except Exception as e:
            print(f"DEBUG AUTH: Auth Exception: {str(e)}")
            raise AuthenticationFailed(str(e))
