"""Django admin configuration for chatbot application models."""

from django.contrib import admin

from .models import Chatbot, Message


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """Admin configuration for the Message model."""

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
    """Admin configuration for the Chatbot model."""

    list_display = ("name", "created_at")
    search_fields = ("name",)
    readonly_fields = ("created_at",)
