import logging
import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

class AddressValidationService:
    """
    Service for validating addresses in Europe and the UK.
    """

    VALIDATION_PROVIDERS = {
        "UK": {
            "name": "Ideal Postcodes",
            "base_url": "https://api.ideal-postcodes.co.uk/v1/postcodes",
            "api_key": getattr(settings, "IDEAL_POSTCODES_API_KEY", None),
        },
        "DE": {
            "name": "Deutsche Post",
            "base_url": "https://postdirekt-invalid-de.herokuapp.com/validate",
            "api_key": getattr(settings, "DEUTSCHE_POST_API_KEY", None),
        },
        "FR": {
            "name": "La Poste",
            "base_url": "https://api.laposte.fr/controladresse/v1",
            "api_key": getattr(settings, "LA_POSTE_API_KEY", None),
        },
    }

    @classmethod
    def validate_address(cls, street_address, postal_code, city, country):
        """
        Validate an address using a country-specific service.

        Args:
            street_address (str): Full street address.
            postal_code (str): Postal/Zip code.
            city (str): City name.
            country (str): Two-letter country code.

        Returns:
            dict: Validation result with status and normalized address.
        """
        country = country.upper()
        cache_key = f"address_validation_{country}_{postal_code}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result

        provider = cls.VALIDATION_PROVIDERS.get(country)
        if not provider or not provider["api_key"]:
            return {
                "is_valid": True,
                "error": f"No validation service available for {country}",
            }

        try:
            response = requests.post(
                provider["base_url"],
                headers={
                    "Authorization": f'Bearer {provider["api_key"]}',
                    "Content-Type": "application/json",
                },
                json={
                    "street": street_address,
                    "postal_code": postal_code,
                    "city": city,
                    "country": country,
                },
                timeout=5,
            )

            if response.status_code == 200:
                result = response.json()
                validation_result = {
                    "is_valid": True,
                    "normalized_address": result.get("normalized_address", {}),
                    "provider": provider["name"],
                }
            else:
                validation_result = {
                    "is_valid": False,
                    "error": response.text,
                    "status_code": response.status_code,
                }

            cache.set(cache_key, validation_result, timeout=86400)
            return validation_result

        except requests.RequestException as e:
            logger.error(f"Address validation error for {country}: {str(e)}")
            return {
                "is_valid": False,
                "error": "Address validation service unavailable",
                "exception": str(e),
            }
