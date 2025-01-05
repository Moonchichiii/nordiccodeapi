from django.contrib import admin

from .models import Chatbot, Message

# Register your models here.


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """Admin view for Message model."""

    list_display = ("user", "user_message", "bot_response", "timestamp")
    search_fields = ("user__username", "user_message", "bot_response")
    readonly_fields = ("timestamp",)


@admin.register(Chatbot)
class ChatbotAdmin(admin.ModelAdmin):
    """Admin view for Chatbot model."""

    list_display = ("name", "created_at")
    search_fields = ("name",)
    readonly_fields = ("created_at",)
