import os
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
import roulette_app.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'roulette_project.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            roulette_app.routing.websocket_urlpatterns
        )
    ),
})