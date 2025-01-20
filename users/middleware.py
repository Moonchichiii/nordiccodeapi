import time
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.http import HttpResponseForbidden


class EuropeanCountryValidationMiddleware:
    """
    Middleware to validate if a country is part of the allowed EU countries.
    """
    ALLOWED_EU_COUNTRIES = [
        "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "GR",
        "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL", "PL", "PT", "RO", "SK",
        "SI", "ES", "SE", "UK",
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    @classmethod
    def validate_country(cls, country_code):
        """
        Validate if the country code is in the allowed EU countries.
        """
        if country_code.upper() not in cls.ALLOWED_EU_COUNTRIES:
            raise ValidationError(f"Country {country_code} is not supported")


class RateLimitMiddleware:
    """
    Middleware to implement rate limiting for authentication attempts.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        """
        Apply rate limiting for login and registration endpoints.
        """
        if request.path in ["/api/auth/login/", "/api/auth/registration/"]:
            ip_address = self.get_client_ip(request)
            cache_key = f"login_attempts_{ip_address}"
            login_attempts = cache.get(cache_key, [])
            current_time = time.time()
            login_attempts = [t for t in login_attempts if current_time - t < 300]

            if len(login_attempts) >= 5:
                return HttpResponseForbidden(
                    "Too many login attempts. Please try again later."
                )

            login_attempts.append(current_time)
            cache.set(cache_key, login_attempts, 300)

        response = self.get_response(request)
        return response

    def get_client_ip(self, request):
        """
        Retrieve the client's IP address from the request.
        """
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip
