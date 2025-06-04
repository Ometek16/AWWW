from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/roulette/$', consumers.RouletteConsumer.as_asgi()),
]