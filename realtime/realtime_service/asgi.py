# ruff: noqa: E402
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "realtime_service.settings")

from channels.routing import ProtocolTypeRouter, URLRouter
from chat.routing import websocket_urlpatterns
from core.middleware import TokenAuthMiddleware

application = ProtocolTypeRouter(
    {
        "websocket": TokenAuthMiddleware(URLRouter(websocket_urlpatterns)),
    }
)
