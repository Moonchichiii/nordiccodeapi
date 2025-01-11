from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from .models import ProjectConversation
from .serializers import ProjectConversationSerializer, ProjectMessageSerializer

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

class ProjectConversationViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectConversationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ProjectConversation.objects.filter(
            Q(project__user=self.request.user)
        ).distinct()

    @action(detail=True, methods=['post'], url_path='send-message')
    def send_message(self, request, pk=None):
        conversation = self.get_object()
        serializer = ProjectMessageSerializer(data=request.data)
        if serializer.is_valid():
            message = serializer.save(
                conversation=conversation,
                sender=request.user
            )
            
            # Broadcast via WebSocket
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'chat_{conversation.id}',
                {
                    'type': 'chat_message',
                    'message': message.content,
                    'user_id': request.user.id,
                    'message_id': message.id,
                    'timestamp': message.created_at.isoformat()
                }
            )
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='mark-read')
    def mark_read(self, request, pk=None):
        conversation = self.get_object()
        messages = conversation.messages.all()
        marked_messages = []
        
        for message in messages:
            if request.user not in message.read_by.all():
                message.read_by.add(request.user)
                marked_messages.append(message.id)

        # Broadcast read status via WebSocket if any messages were marked
        if marked_messages:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'chat_{conversation.id}',
                {
                    'type': 'messages_read',
                    'message_ids': marked_messages,
                    'user_id': request.user.id
                }
            )
        
        return Response(status=status.HTTP_200_OK)