"""
Module to handle signals for the contacts app.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from projects.models import Project
from .models import ProjectConversation

# signals.py
@receiver(post_save, sender=Project)
def create_project_conversation(sender, instance, created, **kwargs):
    if created and instance.status != "planning":
        conversation, created = ProjectConversation.objects.get_or_create(
            project=instance
        )
