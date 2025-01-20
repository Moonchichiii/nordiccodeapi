"""Contact administration module for the Nordic Code API.

This module defines the admin interface configurations for Contact-related models.
"""

from django.contrib import admin
from django.contrib.admin import AdminSite

from .models import MessageAttachment, ProjectConversation, ProjectMessage


class CustomAdminSite(AdminSite):
    """Custom admin site with filtered log entries."""

    def get_log_entries(self, *args, **kwargs):
        """Filter log entries to show only specific action flags.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            QuerySet: Filtered log entries where action_flag is >= 2.
        """
        return super().get_log_entries(*args, **kwargs).filter(action_flag__gte=2)


@admin.register(ProjectConversation)
class ProjectConversationAdmin(admin.ModelAdmin):
    """Admin configuration for ProjectConversation model."""

    list_display = ("project", "created_at", "updated_at", "is_archived")
    search_fields = ("project__title",)
    list_filter = ("is_archived", "updated_at")


@admin.register(ProjectMessage)
class ProjectMessageAdmin(admin.ModelAdmin):
    """Admin configuration for ProjectMessage model."""

    list_display = ("conversation", "sender", "content", "created_at")
    search_fields = ("conversation__project__title", "sender__email", "content")
    list_filter = ("created_at",)


@admin.register(MessageAttachment)
class MessageAttachmentAdmin(admin.ModelAdmin):
    """Admin configuration for MessageAttachment model."""

    list_display = ("message", "file_name", "file_type", "uploaded_at")
    search_fields = ("file_name", "file_type")
    list_filter = ("uploaded_at",)
