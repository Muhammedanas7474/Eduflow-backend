"""
JWT Authentication Middleware for WebSocket connections.

This middleware is stateless - it extracts user info directly from the JWT token
without querying the database. This is necessary because the realtime service
doesn't have access to the core backend's User model.

The token is passed via query string: ws://host/ws/chat/room/?token=<jwt>
"""

from urllib.parse import parse_qs

import jwt
from django.conf import settings


class WebSocketUser:
    """Simple user-like object created from JWT claims."""

    def __init__(self, user_id, tenant_id, role, full_name=""):
        self.id = user_id
        self.tenant_id = tenant_id
        self.role = role
        self.full_name = full_name
        self.is_authenticated = True

    def __str__(self):
        return f"WebSocketUser(id={self.id}, tenant={self.tenant_id}, role={self.role})"


class AnonymousWebSocketUser:
    """Anonymous user for unauthenticated connections."""

    id = None
    tenant_id = None
    role = None
    full_name = ""
    is_authenticated = False

    def __str__(self):
        return "AnonymousWebSocketUser"


class JWTAuthMiddleware:
    """
    ASGI middleware that authenticates WebSocket connections using JWT.

    Extracts the token from the query string and decodes it to get user info.
    Does NOT query the database - all info comes from the JWT claims.
    """

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        # Only process WebSocket connections
        if scope["type"] != "websocket":
            return await self.inner(scope, receive, send)

        query_string = scope.get("query_string", b"").decode()
        params = parse_qs(query_string)
        token = params.get("token", [None])[0]

        if token:
            try:
                # Decode and verify the JWT token
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])

                scope["user"] = WebSocketUser(
                    user_id=payload.get("user_id"),
                    tenant_id=payload.get("tenant_id"),
                    role=payload.get("role"),
                    full_name=payload.get("full_name", ""),
                )

            except jwt.ExpiredSignatureError:
                # Token has expired
                scope["user"] = AnonymousWebSocketUser()
                scope["auth_error"] = "Token expired"

            except jwt.InvalidTokenError as e:
                # Invalid token
                scope["user"] = AnonymousWebSocketUser()
                scope["auth_error"] = f"Invalid token: {str(e)}"
        else:
            scope["user"] = AnonymousWebSocketUser()
            scope["auth_error"] = "No token provided"

        return await self.inner(scope, receive, send)
