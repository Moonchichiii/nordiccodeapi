import logging
import uuid
from django.utils import timezone

class SecurityEventLogger:
    """Centralized logging for security-related events."""

    logger = logging.getLogger("security_events")

    @classmethod
    def log_login_attempt(cls, user_email, success, ip_address):
        """Log login attempts with comprehensive details."""
        event_id = str(uuid.uuid4())
        log_data = {
            "event_id": event_id,
            "event_type": "login_attempt",
            "timestamp": timezone.now(),
            "email": user_email,
            "success": success,
            "ip_address": ip_address,
        }
        cls.logger.info(f"Login Attempt: {log_data}")
        return event_id

    @classmethod
    def log_password_change(cls, user_email, success):
        """Log password change events."""
        event_id = str(uuid.uuid4())
        log_data = {
            "event_id": event_id,
            "event_type": "password_change",
            "timestamp": timezone.now(),
            "email": user_email,
            "success": success,
        }
        cls.logger.warning(f"Password Change: {log_data}")
        return event_id

    @classmethod
    def log_account_creation(cls, user_email, registration_method):
        """Log user account creation."""
        event_id = str(uuid.uuid4())
        log_data = {
            "event_id": event_id,
            "event_type": "account_creation",
            "timestamp": timezone.now(),
            "email": user_email,
            "registration_method": registration_method,
        }
        cls.logger.info(f"Account Creation: {log_data}")
        return event_id

    @classmethod
    def log_security_violation(cls, violation_type, details):
        """Log potential security violations."""
        event_id = str(uuid.uuid4())
        log_data = {
            "event_id": event_id,
            "event_type": "security_violation",
            "timestamp": timezone.now(),
            "violation_type": violation_type,
            "details": details,
        }
        cls.logger.critical(f"Security Violation: {log_data}")
        return event_id
