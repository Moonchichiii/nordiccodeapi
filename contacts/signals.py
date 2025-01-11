"""
Module to handle signals for the contacts app.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from projects.models import Project
from .models import ProjectConversation

@receiver(post_save, sender=Project)
def create_project_conversation(sender, instance, created, **kwargs):
    """
    Signal to create a project conversation when a project is created 
    and the status is not 'planning'.
    """
    if created and instance.status != 'planning':
        conversation, created = ProjectConversation.objects.get_or_create(
            project=instance
        )
        print(
            f"Signal triggered: {'created' if created else 'existing'}, "
            f"Conversation ID: {conversation.id}"
        )
