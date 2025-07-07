import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import AudienceMessage
from debates.models import DebateRoom
from users.models import RoomParticipant

class AudienceChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'audience_chat_{self.room_id}'

        user = self.scope["user"]
        if not await self.is_audience_member(user, self.room_id):
            await self.close()
            return

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, _):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        user = self.scope["user"]
        text_data_json = json.loads(text_data)
        message = text_data_json.get('message')

        if await self.is_audience_member(user, self.room_id):
            msg = await self.save_message(user, message)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'user': user.username,
                    'message': msg.message,
                    'timestamp': msg.timestamp.isoformat(),
                }
            )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def is_audience_member(self, user, room_id):
        return RoomParticipant.objects.filter(user=user, room_id=room_id, role='audience').exists()

    @database_sync_to_async
    def save_message(self, user, message):
        room = DebateRoom.objects.get(id=self.room_id)
        return AudienceMessage.objects.create(room=room, user=user, message=message)
