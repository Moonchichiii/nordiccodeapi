from rest_framework import serializers
from .models import ProjectConversation, ProjectMessage, MessageAttachment


class MessageAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageAttachment
        fields = ["id", "file", "file_name", "file_type", "uploaded_at"]
        read_only_fields = ["uploaded_at"]


class ProjectMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source="sender.full_name", read_only=True)
    sender_email = serializers.CharField(source="sender.email", read_only=True)
    attachments = MessageAttachmentSerializer(many=True, required=False)
    conversation = serializers.PrimaryKeyRelatedField(
        queryset=ProjectConversation.objects.all()
    )
    is_read = serializers.SerializerMethodField()

    class Meta:
        model = ProjectMessage
        fields = [
            "id",
            "conversation",
            "sender",
            "sender_name",
            "sender_email",
            "content",
            "created_at",
            "is_read",
            "has_attachment",
            "attachments",
        ]
        read_only_fields = ["sender", "created_at", "is_read"]

    def get_is_read(self, obj):
        request = self.context.get("request")
        if request and request.user:
            return request.user in obj.read_by.all()
        return False

    def create(self, validated_data):
        """
        Create a new ProjectMessage. If attachments are provided, set has_attachment=True
        and auto-fill file_name/file_type if missing.
        """
        attachments_data = validated_data.pop("attachments", [])
        # If we have any attachments, set has_attachment=True automatically
        has_attachment = bool(attachments_data)

        # Create the message
        message = ProjectMessage.objects.create(
            has_attachment=has_attachment,
            **validated_data
        )

        for attachment_data in attachments_data:
            # Optionally fill out file_name/file_type if the client didn't provide them
            file_obj = attachment_data.get("file")
            if file_obj:
                attachment_data.setdefault("file_name", file_obj.name)
                attachment_data.setdefault("file_type", file_obj.content_type or "application/octet-stream")

            MessageAttachment.objects.create(message=message, **attachment_data)

        return message

    def validate_attachments(self, value):
        """
        Validate the attachments (e.g., file size or file extension).
        """
        for attachment in value:
            # Example: Enforce 10MB max size
            if attachment.file.size > 10 * 1024 * 1024:
                raise serializers.ValidationError("File size cannot exceed 10MB.")
        return value


class ProjectConversationSerializer(serializers.ModelSerializer):
    messages = ProjectMessageSerializer(many=True, read_only=True)
    project_title = serializers.CharField(source="project.title", read_only=True)
    client_name = serializers.CharField(source="project.user.full_name", read_only=True)
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = ProjectConversation
        fields = [
            "id",
            "project",
            "project_title",
            "client_name",
            "messages",
            "unread_count",
            "created_at",
            "updated_at",
        ]

    def get_unread_count(self, obj):
        request = self.context.get("request")
        if request and request.user:
            return obj.messages.exclude(read_by=request.user).count()
        return 0
