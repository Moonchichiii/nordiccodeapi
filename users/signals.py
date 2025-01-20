import logging
from allauth.account.signals import email_confirmation_sent
from django.dispatch import receiver

logger = logging.getLogger("security_events")

@receiver(email_confirmation_sent)
def customize_email_confirmation(sender, request, confirmation, **kwargs):
    """Log email confirmation events and generate confirmation URL."""
    confirmation_key = confirmation.key
    confirmation_url = f"/api/auth/registration/account-confirm-email/{confirmation_key}/"
    
    logger.info(
        "Email confirmation signal sent. Confirmation URL: %s", 
        confirmation_url
    )
