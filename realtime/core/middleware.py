from urllib.parse import parse_qs

import jwt
from django.conf import settings
from django.contrib.auth.models import AnonymousUser


class WebSocketUser:
    """
    Ephemeral user object created from JWT claims.
    No database lookup needed — purely stateless.
    """

    def __init__(self, user_id, tenant_id, role="STUDENT", full_name=""):
        self.id = int(user_id) if user_id is not None else None
        self.pk = self.id
        self.tenant_id = int(tenant_id) if tenant_id is not None else None
        self.role = role
        self.full_name = full_name
        self.is_authenticated = True
        self.is_anonymous = False

    def __str__(self):
        return f"WebSocketUser(id={self.id}, role={self.role})"


class TokenAuthMiddleware:
    """
    Stateless JWT authentication for WebSocket connections.
    Extracts the token from query string, decodes it without DB lookup,
    and creates an ephemeral WebSocketUser.
    """

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        query_string = scope.get("query_string", b"").decode()
        params = parse_qs(query_string)

        token = params.get("token", [None])[0]

        if token:
            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
                scope["user"] = WebSocketUser(
                    user_id=payload.get("user_id"),
                    tenant_id=payload.get("tenant_id"),
                    role=payload.get("role", "STUDENT"),
                    full_name=payload.get("full_name", ""),
                )
            except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
                scope["user"] = AnonymousUser()
        else:
            scope["user"] = AnonymousUser()

        return await self.inner(scope, receive, send)


# Alias for backward compatibility
JWTAuthMiddleware = TokenAuthMiddleware
