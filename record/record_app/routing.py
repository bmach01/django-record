from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r"ws/chat/(?P<channel_id>\d+)/$", consumers.ChatConsumer.as_asgi()),
    re_path(r"ws/channels/(?P<user_id>\d+)/$", consumers.ChannelUpdateConsumer.as_asgi()),
    re_path(r"ws/private/(?P<conversation_id>\d+)/$", consumers.PrivateChatConsumer.as_asgi()),
]
