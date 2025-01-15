from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.shortcuts import get_object_or_404
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import ProjectConversation, ProjectMessage
from .serializers import ProjectConversationSerializer, ProjectMessageSerializer


class ProjectConversationViewSet(viewsets.ModelViewSet):
    """Handles ProjectConversation and ProjectMessage CRUD operations."""
    serializer_class = ProjectConversationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (ProjectConversation.objects
                .filter(project__user=self.request.user)
                .select_related("project")
                .prefetch_related("messages__attachments")
                .distinct())

    @action(detail=True, methods=["post"], url_path="mark-read")
    def mark_read(self, request, pk=None):
        """Mark conversation messages as read."""
        conversation = self.get_object()
        messages = conversation.messages.all()
        marked_messages = []

        for message in messages:
            if request.user not in message.read_by.all():
                message.read_by.add(request.user)
                marked_messages.append(message.id)

        if marked_messages:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"chat_{conversation.id}",
                {
                    "type": "messages_read",
                    "message_ids": marked_messages,
                    "user_id": request.user.id,
                })

        return Response(status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="send-message")
    def send_message(self, request, pk=None):
        """Send a message to a conversation."""
        conversation = self.get_object()
        serializer = ProjectMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = serializer.save(
            sender=self.request.user,
            conversation=conversation)

        # Broadcast the message to the conversation's channel
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"chat_{conversation.id}",
            {
                "type": "chat_message",
                "message": message.content,
                "user_id": message.sender_id,
                "message_id": message.id,
                "timestamp": message.created_at.isoformat(),
            })

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"], url_path="list-messages")
    def list_messages(self, request):
        """List all messages for a specific conversation."""
        conversation_id = request.query_params.get("conversation_id")
        if not conversation_id:
            return Response(
                {"detail": "Conversation ID is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        conversation = get_object_or_404(
            ProjectConversation,
            pk=conversation_id,
            project__user=request.user,
        )
        messages = conversation.messages.select_related("sender").prefetch_related("attachments")
        serializer = ProjectMessageSerializer(messages, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class ProjectMessageViewSet(viewsets.ModelViewSet):
    """ProjectMessage CRUD operations."""
    serializer_class = ProjectMessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (ProjectMessage.objects
            .filter(conversation__project__user=self.request.user)
            .select_related("conversation", "sender")
            .prefetch_related("attachments"))

    def perform_create(self, serializer):
        conversation_id = self.request.data.get("conversation")
        conversation = get_object_or_404(ProjectConversation, pk=conversation_id)
        message = serializer.save(
            sender=self.request.user,
            conversation=conversation)

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"chat_{message.conversation.id}",
            {
                "type": "chat_message",
                "message": message.content,
                "user_id": message.sender_id,
                "message_id": message.id,
                "timestamp": message.created_at.isoformat(),
            })

        return message

