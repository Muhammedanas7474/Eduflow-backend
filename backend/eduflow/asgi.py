# ruff: noqa: E402
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eduflow.settings")

from django.core.asgi import get_asgi_application

# 👇 FIRST initialize Django
django_asgi_app = get_asgi_application()

from apps.notifications.routing import (
    websocket_urlpatterns as notifications_urlpatterns,
)
from channels.routing import ProtocolTypeRouter, URLRouter

from .middleware import TokenAuthMiddleware

websocket_urlpatterns = notifications_urlpatterns

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": TokenAuthMiddleware(URLRouter(websocket_urlpatterns)),
    }
)
