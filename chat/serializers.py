from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .models import MessageAttachment, ProjectConversation, ProjectMessage
from .validators import validate_file_extension, validate_file_size


class MessageAttachmentSerializer(serializers.ModelSerializer):
    """Serializer for MessageAttachment model."""

    file = serializers.FileField(write_only=True)

    class Meta:
        model = MessageAttachment
        fields = ["id", "file", "file_name", "file_type", "uploaded_at"]
        read_only_fields = ["uploaded_at", "file_name", "file_type"]

    def validate_file(self, file):
        """Validate individual file."""
        try:
            validate_file_extension(file)
            validate_file_size(file)
            return file
        except DjangoValidationError as e:
            raise ValidationError(str(e))


class ProjectMessageSerializer(serializers.ModelSerializer):
    """Serializer for ProjectMessage model."""

    sender_name = serializers.CharField(source="sender.full_name", read_only=True)
    sender_email = serializers.CharField(source="sender.email", read_only=True)
    attachments = MessageAttachmentSerializer(many=True, required=False, read_only=True)
    files = serializers.ListField(
        child=serializers.FileField(max_length=100000, allow_empty_file=False),
        write_only=True,
        required=False,
    )
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
            "files",
        ]
        read_only_fields = ["sender", "created_at", "is_read", "has_attachment"]

    def validate_files(self, files):
        """Validate all files."""
        validated_files = []
        for file in files:
            attachment_serializer = MessageAttachmentSerializer(data={"file": file})
            attachment_serializer.is_valid(raise_exception=True)
            validated_files.append(file)
        return validated_files

    def get_is_read(self, obj):
        """Check if the message is read by the user."""
        request = self.context.get("request")
        if request and request.user:
            return request.user in obj.read_by.all()
        return False

    def create(self, validated_data):
        """Create a new ProjectMessage with optional attachments."""
        # Remove files from validated data if present
        files = validated_data.pop("files", [])

        # Remove has_attachment if present to avoid duplicate argument
        validated_data.pop("has_attachment", None)

        # Create message
        message = ProjectMessage.objects.create(
            has_attachment=bool(files), **validated_data
        )

        # Create attachments
        for file in files:
            MessageAttachment.objects.create(
                message=message,
                file=file,
                file_name=file.name,
                file_type=file.content_type or "application/octet-stream",
            )

        return message


class ProjectConversationSerializer(serializers.ModelSerializer):
    """Serializer for ProjectConversation model."""

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
        """Get the count of unread messages."""
        request = self.context.get("request")
        if request and request.user:
            return obj.messages.exclude(read_by=request.user).count()
        return 0
