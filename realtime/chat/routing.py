from django.urls import re_path

from .consumers import ChatConsumer
from .video_consumers import VideoCallConsumer

websocket_urlpatterns = [
    re_path(r"ws/chat/(?P<room_name>\w+)/$", ChatConsumer.as_asgi()),
    re_path(r"ws/call/(?P<room_id>\w+)/$", VideoCallConsumer.as_asgi()),
]
