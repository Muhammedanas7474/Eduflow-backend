# ruff: noqa: E402
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "realtime_service.settings")

import django

django.setup()

from channels.routing import ProtocolTypeRouter, URLRouter
from chat.routing import websocket_urlpatterns
from core.middleware import TokenAuthMiddleware
from django.core.asgi import get_asgi_application

application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": TokenAuthMiddleware(URLRouter(websocket_urlpatterns)),
    }
)
