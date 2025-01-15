from django.db import models
from django.conf import settings
from .validators import validate_file_extension, validate_file_size


class ProjectConversation(models.Model):
    """
    Represents a conversation thread for an active project.
    Only created when a project moves to active status after deposit payment.
    """

    project = models.OneToOneField(
        "projects.Project", on_delete=models.CASCADE, related_name="conversation"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_archived = models.BooleanField(default=False)

    class Meta:
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["-updated_at"]),
            models.Index(fields=["project", "-updated_at"]),
        ]

    def __str__(self):
        return f"Conversation for {self.project.title}"

    def get_participants(self):
        """Get all participants in the conversation (client and staff)"""
        return [self.project.user] + list(self.staff_participants.all())


class ProjectMessage(models.Model):
    """
    Individual messages within a project conversation.
    """

    conversation = models.ForeignKey(
        ProjectConversation, on_delete=models.CASCADE, related_name="messages"
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_project_messages",
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    read_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="read_messages"
    )
    has_attachment = models.BooleanField(default=False)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["conversation", "created_at"]),
            models.Index(fields=["sender", "created_at"]),
        ]

    def __str__(self):
        return f"Message from {self.sender.email} at {self.created_at}"

    def mark_read_by(self, user):
        """Mark message as read by a user"""
        self.read_by.add(user)


class MessageAttachment(models.Model):
    """
    Attachments for project messages.
    """

    message = models.ForeignKey(
        ProjectMessage, on_delete=models.CASCADE, related_name="attachments"
    )
    file = models.FileField(
        upload_to="project_messages/%Y/%m/",
        validators=[validate_file_size, validate_file_extension],
    )
    file_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=100)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file_name
