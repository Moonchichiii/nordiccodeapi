import aiohttp
import logging
import uuid
from typing import Any, Dict

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.mail import send_mail
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

logger = logging.getLogger(__name__)


class TokenService:
    """Service for handling JWT tokens."""

    @staticmethod
    def _create_token_payload(user, token_type: str, token_id: str = None) -> Dict[str, Any]:
        """Create payload for JWT token."""
        return {
            'token_type': token_type,
            'jti': token_id or str(uuid.uuid4()),
            'iat': timezone.now().timestamp(),
            'user_id': str(user.id),
            'email': user.email,
            'is_verified': user.is_verified,
        }

    @classmethod
    def get_tokens_for_user(cls, user) -> Dict[str, str]:
        """Generate refresh and access tokens for a user."""
        refresh = RefreshToken.for_user(user)
        token_id = str(uuid.uuid4())
        refresh.payload.update(cls._create_token_payload(user, 'refresh', token_id))
        access = refresh.access_token
        access.payload.update(cls._create_token_payload(user, 'access'))

        return {
            'refresh': str(refresh),
            'access': str(access),
        }

    @staticmethod
    def revoke_user_tokens(user) -> None:
        """Revoke all tokens for a user."""
        RefreshToken.objects.filter(user=user).delete()


class SecurityService:
    """Service for handling security-related tasks."""

    MAX_ATTEMPTS = 5
    LOCKOUT_DURATION = 900

    @classmethod
    def check_login_attempts(cls, email: str, ip_address: str = None) -> bool:
        """Check and manage login attempts."""
        key = f"login_attempts_{email if email else ip_address}"
        attempts = cache.get(key, 0)
        if attempts >= cls.MAX_ATTEMPTS:
            if email:
                UserModel = get_user_model()
                try:
                    user = UserModel.objects.get(email=email)
                    user.is_active = False
                    user.save()
                except UserModel.DoesNotExist:
                    pass
            return False
        cache.set(key, attempts + 1, cls.LOCKOUT_DURATION)
        return True

    @classmethod
    def reset_attempts(cls, identifier: str) -> None:
        """Reset login attempts for a given identifier."""
        cache.delete(f"login_attempts_{identifier}")

    @classmethod
    def unlock_account(cls, email: str) -> bool:
        """Unlock a user's account."""
        UserModel = get_user_model()
        try:
            user = UserModel.objects.get(email=email)
            user.is_active = True
            user.save()
            cls.reset_attempts(email)
            return True
        except UserModel.DoesNotExist:
            return False

    @classmethod
    def log_security_event(cls, event_type: str, data: Dict[str, Any]) -> str:
        """Log a security event."""
        event_id = str(uuid.uuid4())
        log_data = {
            "event_id": event_id,
            "event_type": event_type,
            "timestamp": timezone.now(),
            **data
        }
        logger.info(f"Security Event: {log_data}")
        return event_id


class AddressService:
    """Service for handling address validation for European operations."""

    # This is good - keeps all EU countries as boundaries
    ALLOWED_EU_COUNTRIES = [
        "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "GR",
        "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL", "PL", "PT", "RO", "SK",
        "SI", "ES", "SE", "UK",
    ]

    # Keep the full EU name mapping for user-friendly input
    COUNTRY_NAME_TO_ISO = {
        "Austria": "AT",
        "Belgium": "BE",
        "Bulgaria": "BG",
        "Croatia": "HR",
        "Cyprus": "CY",
        "Czech Republic": "CZ",
        "Denmark": "DK",
        "Estonia": "EE",
        "Finland": "FI",
        "France": "FR",
        "Germany": "DE",
        "Greece": "GR",
        "Hungary": "HU",
        "Ireland": "IE",
        "Italy": "IT",
        "Latvia": "LV",
        "Lithuania": "LT",
        "Luxembourg": "LU",
        "Malta": "MT",
        "Netherlands": "NL",
        "Poland": "PL",
        "Portugal": "PT",
        "Romania": "RO",
        "Slovakia": "SK",
        "Slovenia": "SI",
        "Spain": "ES",
        "Sweden": "SE",
        "United Kingdom": "UK",
        "Norway": "NO",
    }

    @classmethod
    def validate_country(cls, country_code: str) -> bool:
        """Validate if the country is allowed."""
        name = country_code.strip().title()
        if name in cls.COUNTRY_NAME_TO_ISO:
            country_code = cls.COUNTRY_NAME_TO_ISO[name]
        country_code = country_code.upper()
        if country_code not in cls.ALLOWED_EU_COUNTRIES:
            raise ValidationError(f"Sorry, we currently only operate within the EU")
        return True

    @classmethod
    async def validate_address(cls, street_address: str, postal_code: str, city: str, country: str) -> Dict[str, Any]:
        """Validate the address using Nominatim."""
        country = country.strip()
        try:
            cls.validate_country(country)
        except ValidationError as e:
            logger.warning(f"Address validation: {e}")
            return {"is_valid": False, "error": str(e)}

        # Check cache first
        cache_key = f"address_validation_{country.upper()}_{postal_code}_{street_address}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result

        try:
            search_query = f"{street_address}, {postal_code} {city}, {country}"
            params = {
                'q': search_query,
                'format': 'json',
                'addressdetails': 1,
                'limit': 1
            }
            headers = {
                'User-Agent': settings.ADDRESS_VALIDATION['NOMINATIM_USER_AGENT']
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://nominatim.openstreetmap.org/search",
                    params=params,
                    headers=headers,
                    timeout=10
                ) as response:
                    if response.status == 200:
                        results = await response.json()
                        if results:
                            validation_result = {
                                "is_valid": True,
                                "normalized_address": results[0],
                                "confidence": float(results[0].get('importance', 0))
                            }
                            cache.set(cache_key, validation_result, timeout=86400)
                            return validation_result

                    return {
                        "is_valid": False,
                        "error": "Address not found or invalid"
                    }

        except Exception as e:
            logger.error(f"Address validation error for {country}: {str(e)}")
            return {
                "is_valid": False,
                "error": "Address validation service unavailable"
            }

class EmailService:
    """Service for handling email-related tasks."""

    @staticmethod
    def send_activation_email(user, activation_link: str) -> None:
        """Send activation email to the user."""
        subject = "Verify your account"
        message = (
            f"Hi {user.full_name},\n\n"
            f"Please click the link below to verify your account:\n"
            f"{activation_link}\n\n"
            "This link will expire in 4 hours.\n\n"
            "Thank you!"
        )
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
        SecurityService.log_security_event('email_sent', {'email': user.email, 'type': 'activation'})
