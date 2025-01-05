import logging

from django.conf import settings
from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Contact

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Contact)
def send_contact_email(sender, instance, created, **kwargs):
    """
    Sends an email notification when a new Contact instance is created.
    """
    if created:
        try:
            send_mail(
                subject=f"New Contact from {instance.name}",
                message=f"Message:\n{instance.message}\n\nEmail: {instance.email}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.DEFAULT_FROM_EMAIL],
                fail_silently=False,
            )
        except Exception as e:
            logger.error(f"Error sending email: {e}")
