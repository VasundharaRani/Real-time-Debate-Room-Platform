from channels.generic.websocket import AsyncWebsocketConsumer
import json

class DebateConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        print("Connected user:", self.scope["user"]) 
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f"debate_{self.room_id}"
        self.user = self.scope['user']
    

        # Add websocket connection to room's group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        # notify the group that user has joined
        await self.channel_layer.group_send(
            self.room_group_name,{
                'type' : 'user_joined',
                'user_id' : self.user.id,
                'username' : self.user.username
            }
        )

    async def disconnect(self, close_code):
        # notify the group that user has left
        await self.channel_layer.group_send(
            self.room_group_name,{
                'type' : 'user_left',
                'user_id' : self.user.id
            }
        )
        # remove websocket connection from the group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data) #parses messgaes from json format into python dict
        action = data.get('action') #reads the type action from the message

        # handling webRTC signaling
        if action == 'signal':
            await self.channel_layer.group_send(
                self.room_group_name,{
                    'type' : 'signal.message',
                    'user_id' : self.user.id,
                    'target_id' : data['target_id'],
                    'signal_data' : data['signal_data'] 
                }
            )
        elif action == 'mute_user':
            await self.channel_layer.group_send(
                self.room_group_name,{
                    'type' : 'moderator.mute',
                    'target_id' : data['target_id']
                }
            )

    async def signal_message(self,event):
        print(f"Signal to {self.user.id} from {event['user_id']} of type {event['signal_data'].get('type')}")
        if str(self.user.id) == str(event['target_id']):
            await self.send(text_data = json.dumps({
                'action' : 'signal',
                'from_id' : event['user_id'],
                'signal_data' : event['signal_data']
            }))

    async def user_joined(self,event):
        await self.send(text_data = json.dumps({
            'action' : 'user_joined',
            'user_id' : event['user_id'],
            'username' : event['username']
        }))

    async def user_left(self,event):
        await self.send(text_data = json.dumps({
            'action' : 'user_left',
            'user_id' : event['user_id']
        }))
    
    async def moderator_mute(self,event):
        await self.send(text_data = json.dumps({
            'action' : 'mute',
            'user_id' : event['target_id']
        }))