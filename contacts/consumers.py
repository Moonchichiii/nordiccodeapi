import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ProjectConversation as Conversation, ProjectMessage as Message


class MessageConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if self.scope["user"].is_authenticated:
            self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
            self.room_group_name = f'chat_{self.conversation_id}'

            # Join room group
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            await self.accept()
        else:
            await self.close(code=401)  # Close connection for unauthenticated users

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json.get('message', '')

        if len(message) > 1000:  # Example limit
            await self.send(text_data=json.dumps({
                'error': 'Message too long'
            }))
            return

        user_id = self.scope["user"].id

        # Save message to database
        try:
            saved_message = await self.save_message(user_id, message)
        except ValueError as e:
            await self.send(text_data=json.dumps({
                'error': str(e)
            }))
            return

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'user_id': user_id,
                'message_id': saved_message.id,
                'timestamp': saved_message.created_at.isoformat()
            }
        )

    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'user_id': event['user_id'],
            'message_id': event['message_id'],
            'timestamp': event['timestamp']
        }))

    @database_sync_to_async
    def save_message(self, user_id, content):
        try:
            conversation = Conversation.objects.get(id=self.conversation_id)
            message = Message.objects.create(
                conversation=conversation,
                sender_id=user_id,
                content=content
            )
            return message
        except Conversation.DoesNotExist:
            # Log error or take appropriate action
            raise ValueError("Invalid conversation ID")