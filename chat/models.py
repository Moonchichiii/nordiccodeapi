from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from .validators import validate_file_extension, validate_file_size


class ProjectConversation(models.Model):
    """Conversation for a project.

    Attributes:
        project: The project associated with the conversation.
        created_at: The date and time when the conversation was created.
        updated_at: The date and time when the conversation was last updated.
        is_archived: Boolean indicating if the conversation is archived.
    """

    project = models.OneToOneField(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="conversation"
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

    def __str__(self) -> str:
        """Return conversation info."""
        return f"Conversation for {self.project.title}"

    def get_participants(self) -> list:
        """Return participants."""
        return [self.project.user] + list(self.staff_participants.all())

    def unread_count(self, user: settings.AUTH_USER_MODEL) -> int:
        """Return unread messages count."""
        return self.messages.exclude(read_by=user).count()


class ProjectMessage(models.Model):
    """Message in a project conversation.

    Attributes:
        conversation: The conversation to which the message belongs.
        sender: The user who sent the message.
        content: The content of the message.
        created_at: The date and time when the message was created.
        read_by: Users who have read the message.
        has_attachment: Boolean indicating if the message has an attachment.
    """

    conversation = models.ForeignKey(
        ProjectConversation,
        on_delete=models.CASCADE,
        related_name="messages"
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_project_messages"
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    read_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="read_messages"
    )
    has_attachment = models.BooleanField(default=False)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["conversation", "created_at"]),
            models.Index(fields=["sender", "created_at"]),
        ]

    def __str__(self) -> str:
        """Return message info."""
        return f"Message from {self.sender.email} at {self.created_at}"

    def mark_read_by(self, user: settings.AUTH_USER_MODEL) -> None:
        """Mark message read by user."""
        self.read_by.add(user)

    @classmethod
    def mark_messages_read(cls, conversation: ProjectConversation,
                           user: settings.AUTH_USER_MODEL) -> None:
        """Bulk mark messages as read."""
        for msg in conversation.messages.exclude(read_by=user):
            msg.read_by.add(user)


class MessageAttachment(models.Model):
    """Attachment for a project message.

    Attributes:
        message: The message to which the attachment belongs.
        file: The file attached to the message.
        file_name: The name of the file.
        file_type: The type of the file.
        uploaded_at: The date and time when the file was uploaded.
    """

    message = models.ForeignKey(
        "chat.ProjectMessage",
        on_delete=models.CASCADE,
        related_name="attachments"
    )
    file = models.FileField(
        upload_to="attachments/",
        validators=[validate_file_extension, validate_file_size]
    )
    file_name = models.CharField(max_length=255, blank=True)
    file_type = models.CharField(max_length=100, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["message", "uploaded_at"]),
        ]

    def __str__(self) -> str:
        """Return file name."""
        return self.file_name
