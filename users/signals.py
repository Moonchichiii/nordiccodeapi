from django.conf import settings
from django.dispatch import receiver
from allauth.account.signals import email_confirmation_sent
from allauth.account.adapter import get_adapter

import logging

logger = logging.getLogger('django.dispatch')

@receiver(email_confirmation_sent)
def customize_email_confirmation(sender, request, confirmation, **kwargs):
    logger = logging.getLogger('django.dispatch')
    logger.info("Signal sent: email_confirmation_sent")
    confirmation_key = confirmation.key
    confirmation_url = f"{settings.ACCOUNT_EMAIL_CONFIRMATION_AUTHENTICATED_REDIRECT_URL}/confirm-email/{confirmation_key}"
    get_adapter(request).send_mail(
        "account/email_confirmation",
        confirmation.email_address.email,
        {"activate_url": confirmation_url},
    )
