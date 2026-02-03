import os

from apps.notifications.routing import (
    websocket_urlpatterns as notifications_urlpatterns,
)
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from eduflow.middleware import TokenAuthMiddleware

# Environment setup AFTER imports
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eduflow.settings")

# Initialize Django
django_asgi_app = get_asgi_application()

# Re-export websocket patterns (logic unchanged)
websocket_urlpatterns = notifications_urlpatterns

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": TokenAuthMiddleware(URLRouter(websocket_urlpatterns)),
    }
)
