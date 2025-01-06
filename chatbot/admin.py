"""Django admin configuration for chatbot application models."""
from django.contrib import admin

from .models import Chatbot, Message


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Message model.

    Attributes:
        list_display: Fields to display in the admin list view
        search_fields: Fields available for searching
        readonly_fields: Fields that cannot be modified
    """

    list_display = (
        "user",
        "user_message",
        "bot_response",
        "timestamp",
    )
    search_fields = (
        "user__username",
        "user_message",
        "bot_response",
    )
    readonly_fields = ("timestamp",)


@admin.register(Chatbot)
class ChatbotAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Chatbot model.

    Attributes:
        list_display: Fields to display in the admin list view
        search_fields: Fields available for searching
        readonly_fields: Fields that cannot be modified
    """

    list_display = ("name", "created_at")
    search_fields = ("name",)
    readonly_fields = ("created_at",)
