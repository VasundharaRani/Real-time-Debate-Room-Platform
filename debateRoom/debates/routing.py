from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path("ws/debate/<str:room_id>/", consumers.DebateConsumer.as_asgi()),
]