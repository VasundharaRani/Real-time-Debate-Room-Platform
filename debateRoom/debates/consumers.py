from channels.generic.websocket import AsyncWebsocketConsumer
import json

class ModeratorControlConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.group_name = f"room_{self.room_id}_control"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')
        target_user_id = data.get('target_user_id')

        # Only allow mute and kick from moderator, no unmute
        if action in ["mute", "kick"]:
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "moderator_control",
                    "action": action,
                    "target_user_id": int(target_user_id),
                }
            )
        elif data.get("type") == "self-unmute":
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "self_unmute_broadcast",
                    "user_id": self.scope["user"].id,
                    "username": self.scope["user"].username
                }
            )

    async def moderator_control(self, event):
        await self.send(text_data=json.dumps({
            "type": "moderator-control",
            "action": event["action"],
            "target_user_id": event["target_user_id"],
        }))

    async def self_unmute_broadcast(self, event):
        await self.send(text_data=json.dumps({
            "type": "self-unmute",
            "user_id": event["user_id"],
            "username": event["username"]
        }))
