from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/chat/<int:room_id>/', consumers.AudienceChatConsumer.as_asgi()),
]
