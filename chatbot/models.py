from django.contrib.auth.models import User
from django.db import models

from .hash import hash_message

# Create your models here.


class Chatbot(models.Model):
    """Represents a chatbot."""

    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Message(models.Model):
    """Represents a message exchanged with the chatbot."""

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    chatbot = models.ForeignKey("Chatbot", on_delete=models.CASCADE)
    user_message = models.TextField()
    bot_response = models.TextField(blank=True, null=True)
    user_message_hash = models.CharField(max_length=64)
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=50, choices=[("SUCCESS", "Success"), ("ERROR", "Error")]
    )

    class Meta:
        verbose_name = "Message"
        verbose_name_plural = "Messages"
        ordering = ["-timestamp"]

    def __str__(self):
        return f"Message at {self.timestamp}"

    def save(self, *args, **kwargs):
        """Hashes the message if not already hashed."""
        if not self.user_message_hash:
            self.user_message_hash = hash_message(self.user_message)
        super().save(*args, **kwargs)
