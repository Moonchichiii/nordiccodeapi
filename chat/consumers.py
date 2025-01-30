import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.core.cache import cache

from .models import ProjectConversation as Conversation
from .models import ProjectMessage as Message


class MessageConsumer(AsyncWebsocketConsumer):
    """Handles WebSocket connections for chat messages."""

    async def connect(self) -> None:
        """Establish connection for authenticated users."""
        if self.scope["user"].is_authenticated:
            self.conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]
            self.room_group_name = f"chat_{self.conversation_id}"
            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
            await self.accept()
        else:
            await self.close(code=401)

    async def disconnect(self, close_code: int) -> None:
        """Leave the group when the connection is closed."""
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data: str) -> None:
        """Handle incoming messages and broadcast them."""
        text_data_json = json.loads(text_data)
        message = text_data_json.get("message", "")

        if len(message) > 1000:
            await self.send(text_data=json.dumps({"error": "Message too long"}))
            return

        user_id = self.scope["user"].id

        try:
            saved_message = await self.save_message(user_id, message)
        except ValueError as e:
            await self.send(text_data=json.dumps({"error": str(e)}))
            return

        await self.mark_as_read(saved_message)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": message,
                "user_id": user_id,
                "message_id": saved_message.id,
                "timestamp": saved_message.created_at.isoformat(),
            },
        )

    async def chat_message(self, event: dict) -> None:
        """Send the message to WebSocket clients."""
        await self.send(
            text_data=json.dumps(
                {
                    "message": event["message"],
                    "user_id": event["user_id"],
                    "message_id": event["message_id"],
                    "timestamp": event["timestamp"],
                }
            )
        )

    @database_sync_to_async
    def save_message(self, user_id: int, content: str) -> Message:
        """Save the message to the database."""
        try:
            conversation = Conversation.objects.get(id=self.conversation_id)
            message = Message.objects.create(
                conversation=conversation, sender_id=user_id, content=content
            )
            return message
        except Conversation.DoesNotExist:
            raise ValueError("Invalid conversation ID")

    @database_sync_to_async
    def mark_as_read(self, message: Message) -> None:
        """Mark the message as read by the sender."""
        message.read_by.add(message.sender)
        message.save()

    @database_sync_to_async
    def update_message_count_in_redis(self) -> None:
        """Update the message count in Redis for the conversation."""
        cache_key = f"conversation_{self.conversation_id}_message_count"
        message_count = Message.objects.filter(
            conversation_id=self.conversation_id
        ).count()
        cache.set(cache_key, message_count, timeout=60 * 5)
