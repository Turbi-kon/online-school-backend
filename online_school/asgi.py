"""
ASGI config for online_school project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack



os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'online_school.settings')


django_asgi = get_asgi_application()

import communication.routing
from communication.middleware import TokenAuthMiddleware

application = ProtocolTypeRouter({
    "http": django_asgi,  # Используем ASGI приложение для HTTP
    "websocket": TokenAuthMiddleware(
        URLRouter(
            communication.routing.websocket_urlpatterns  # Роутинг для WebSocket
        )
    ),
})