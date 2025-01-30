import logging
from typing import Any, Dict

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from django_ratelimit.decorators import ratelimit
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ProjectConversation, ProjectMessage
from .serializers import ProjectConversationSerializer, ProjectMessageSerializer

logger = logging.getLogger(__name__)


class ProjectMessagePagination(PageNumberPagination):
    """Pagination for ProjectMessages."""
    page_size = 20


class ProjectMessageViewSet(viewsets.ModelViewSet):
    """Handles ProjectMessage CRUD operations and WebSocket message handling."""
    serializer_class = ProjectMessageSerializer
    pagination_class = ProjectMessagePagination

    def get_queryset(self) -> Any:
        """Get queryset for ProjectMessage."""
        return (
            ProjectMessage.objects.filter(
                conversation__project__user=self.request.user
            )
            .select_related("conversation", "sender")
            .prefetch_related("attachments", "read_by")
        )

    @ratelimit(key="ip", rate="10/m", method="ALL")
    def perform_create(self, serializer: ProjectMessageSerializer) -> ProjectMessage:
        """Handle message creation with rate limiting."""
        conversation_id = self.request.data.get("conversation")
        conversation = get_object_or_404(ProjectConversation, pk=conversation_id)
        message = serializer.save(
            sender=self.request.user, conversation=conversation
        )
        self._broadcast_message(conversation, message)
        return message

    def _broadcast_message(
        self, conversation: ProjectConversation, message: ProjectMessage
    ) -> None:
        """Broadcast the message to WebSocket channel."""
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"chat_{conversation.id}",
            {
                "type": "chat_message",
                "message": message.content,
                "message_id": message.id,
            },
        )

    @action(detail=False, methods=["get"], url_path="list-messages")
    def list_messages(self, request: Any) -> Response:
        """List all messages for a specific conversation."""
        conversation_id = request.query_params.get("conversation_id")
        if not conversation_id:
            return Response(
                {"detail": "Conversation ID is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        conversation = get_object_or_404(
            ProjectConversation, pk=conversation_id, project__user=request.user
        )
        messages = conversation.messages.select_related("sender").prefetch_related(
            "attachments", "read_by"
        )
        serializer = ProjectMessageSerializer(messages, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="mark-read")
    def mark_read(self, request: Any, pk: int = None) -> Response:
        """Mark all messages in a conversation as read."""
        conversation = self.get_object()
        messages = conversation.messages.exclude(read_by=request.user)
        if messages.exists():
            messages.update(read_by=request.user)
            self._notify_read_messages(conversation, messages)
        return Response(status=status.HTTP_200_OK)

    def _notify_read_messages(
        self, conversation: ProjectConversation, messages: Any
    ) -> None:
        """Notify WebSocket group about read messages."""
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"chat_{conversation.id}",
            {
                "type": "messages_read",
                "message_ids": [message.id for message in messages],
                "user_id": self.request.user.id,
            },
        )


class ProjectConversationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Handles ProjectConversation read-only operations.
    Conversations are automatically created via signals.
    """
    serializer_class = ProjectConversationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> Any:
        """Get queryset for ProjectConversation with caching."""
        conversation_cache_key = f"conversations_{self.request.user.id}"
        conversations = cache.get(conversation_cache_key)

        if not conversations:
            conversations = (
                ProjectConversation.objects.filter(project__user=self.request.user)
                .select_related("project")
                .prefetch_related("messages__attachments")
            )
            cache.set(conversation_cache_key, conversations, timeout=60 * 5)

        return conversations


class MarkConversationReadView(APIView):
    """Mark all messages in a conversation as read."""
    permission_classes = [IsAuthenticated]

    def post(self, request: Any, pk: int) -> Response:
        try:
            conversation = ProjectConversation.objects.get(pk=pk)
            for message in conversation.messages.exclude(read_by=request.user):
                message.mark_read_by(request.user)
            return Response({"detail": "All messages marked as read."}, status=200)
        except ProjectConversation.DoesNotExist:
            return Response({"detail": "Conversation not found."}, status=404)
