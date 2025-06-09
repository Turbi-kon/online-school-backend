from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/communication/channels/(?P<channel_id>\d+)/$', consumers.ChannelConsumer.as_asgi()),
    re_path(r'ws/notifications/(?P<user_id>\d+)/$', consumers.NotificationConsumer.as_asgi()),
]
