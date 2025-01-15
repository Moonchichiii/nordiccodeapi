"""Signal handlers for user-related events."""

import logging

from django.conf import settings
from django.dispatch import receiver
from allauth.account.signals import email_confirmation_sent
from allauth.account.adapter import get_adapter


logger = logging.getLogger("django.dispatch")


@receiver(email_confirmation_sent)
def customize_email_confirmation(sender, request, confirmation, **kwargs):
    """Customize email confirmation process."""
    logger = logging.getLogger("django.dispatch")
    logger.info("Signal sent: %s", "email_confirmation_sent")
    confirmation_key = confirmation.key
    base_url = settings.ACCOUNT_EMAIL_CONFIRMATION_AUTHENTICATED_REDIRECT_URL
    confirmation_url = f"{base_url}/confirm-email/{confirmation_key}"
    get_adapter(request).send_mail(
        "account/email_confirmation",
        confirmation.email_address.email,
        {"activate_url": confirmation_url},
    )
