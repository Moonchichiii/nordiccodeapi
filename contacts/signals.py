"""
Signal handlers for Contact model to handle email notifications.

This module contains signal receivers that handle post-save operations
for Contact model instances, specifically sending email notifications.
"""

import logging
from django.conf import settings
from django.core.mail import send_mail
from django.core.exceptions import BadHeaderError
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Contact


logger = logging.getLogger(__name__)


@receiver(post_save, sender=Contact)
def send_contact_email(sender, instance, created, **kwargs):
    """
    Send an email notification when a new Contact instance is created.

    Args:
        sender: The model class that sent the signal
        instance: The actual instance being saved
        created (bool): True if a new record was created
        **kwargs: Additional keyword arguments

    Returns:
        None
    """
    if not created:
        return

    subject = "New Contact from {}".format(instance.name)
    message = "Message:\n{}\n\nEmail: {}".format(
        instance.message,
        instance.email
    )

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.DEFAULT_FROM_EMAIL],
            fail_silently=False,
        )
    except (BadHeaderError, ConnectionError) as exc:
        logger.error("Error sending email: %s", exc)
