from django.test import RequestFactory, TestCase
from django.core.exceptions import ValidationError
from django.core.cache import cache
from django.contrib.auth import get_user_model
from unittest.mock import patch
from allauth.account.models import EmailConfirmation
from django.http import HttpResponse
from users.middleware import RateLimitMiddleware, EuropeanCountryValidationMiddleware
from users.serializers import CustomRegisterSerializer
from users.lockout import AccountLockoutService
from users.security_logging import SecurityEventLogger

User = get_user_model()


class CustomRegisterSerializerAdditionalTests(TestCase):
    def setUp(self):
        cache.clear()
        self.valid_data = {
            "email": "newuser@example.com",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
            "full_name": "Test User",
            "accepted_terms": True,
            "phone_number": "+1234567890",
            "street_address": "123 Test St",
            "city": "Test City",
            "postal_code": "12345",
            "country": "GB",
        }

    def test_validate_invalid_email_format(self):
        invalid_data = self.valid_data.copy()
        invalid_data["email"] = "invalid-email-format"
        serializer = CustomRegisterSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)

    def test_validate_invalid_phone_number(self):
        invalid_data = self.valid_data.copy()
        invalid_data["phone_number"] = "123"
        serializer = CustomRegisterSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("phone_number", serializer.errors)

    def test_missing_required_fields(self):
        required_fields = [
            "email",
            "password1",
            "password2",
            "full_name",
            "accepted_terms",
        ]
        for field in required_fields:
            invalid_data = self.valid_data.copy()
            invalid_data.pop(field)
            serializer = CustomRegisterSerializer(data=invalid_data)
            self.assertFalse(serializer.is_valid())
            self.assertIn(field, serializer.errors)


class EmailSignalTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(
            email="testuser@example.com", password="testpassword123"
        )

    @patch("users.signals.logger")
    def test_email_confirmation_sent_signal(self, mock_logger):
        confirmation = EmailConfirmation.create(
            email_address=self.user.emailaddress_set.create()
        )
        confirmation.send()
        mock_logger.info.assert_called_once()


class RateLimitMiddlewareTests(TestCase):
    def setUp(self):
        cache.clear()
        self.factory = RequestFactory()
        self.middleware = RateLimitMiddleware(
            lambda request: HttpResponse("OK", status=200)
        )

    def test_rate_limit_allows_under_limit(self):
        request = self.factory.post("/api/auth/login/")
        response = self.middleware(request)
        self.assertEqual(response.status_code, 200)

    def test_rate_limit_blocks_over_limit(self):
        request = self.factory.post("/api/auth/login/")
        for _ in range(5):
            response = self.middleware(request)
            self.assertEqual(response.status_code, 200)

        response = self.middleware(request)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.content.decode(),
            "Too many login attempts. Please try again later.",
        )


class EuropeanCountryValidationMiddlewareTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_validate_allowed_country(self):
        middleware = EuropeanCountryValidationMiddleware(lambda x: x)
        try:
            middleware.validate_country("FR")
        except ValidationError:
            self.fail("Validation raised an exception for an allowed country.")

    def test_validate_disallowed_country(self):
        middleware = EuropeanCountryValidationMiddleware(lambda x: x)
        with self.assertRaises(ValidationError):
            middleware.validate_country("US")


class AccountLockoutServiceTests(TestCase):
    def setUp(self):
        cache.clear()
        self.email = "lockout_test@example.com"
        self.user = User.objects.create_user(
            email=self.email, password="testpassword123"
        )

    def test_increment_login_attempts(self):
        for _ in range(AccountLockoutService.MAX_LOGIN_ATTEMPTS):
            allowed = AccountLockoutService.check_and_update_login_attempts(self.email)
            self.assertTrue(allowed)

    def test_account_lockout_after_max_attempts(self):
        for _ in range(AccountLockoutService.MAX_LOGIN_ATTEMPTS + 1):
            allowed = AccountLockoutService.check_and_update_login_attempts(self.email)
        self.assertFalse(allowed)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)

    def test_unlock_account(self):
        AccountLockoutService.check_and_update_login_attempts(self.email)
        self.user.is_active = False
        self.user.save()
        unlocked = AccountLockoutService.unlock_account(self.email)
        self.assertTrue(unlocked)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)

    def test_reset_login_attempts(self):
        AccountLockoutService.check_and_update_login_attempts(self.email)
        AccountLockoutService.reset_login_attempts(self.email)
        cached_attempts = cache.get(f"login_attempts_{self.email}")
        self.assertIsNone(cached_attempts)


class SecurityEventLoggerTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_log_login_attempt(self):
        event_id = SecurityEventLogger.log_login_attempt(
            user_email="test@example.com", success=True, ip_address="127.0.0.1"
        )
        self.assertIsNotNone(event_id)

    def test_log_password_change(self):
        event_id = SecurityEventLogger.log_password_change(
            user_email="test@example.com", success=True
        )
        self.assertIsNotNone(event_id)

    def test_log_account_creation(self):
        event_id = SecurityEventLogger.log_account_creation(
            user_email="test@example.com", registration_method="email"
        )
        self.assertIsNotNone(event_id)

    def test_log_security_violation(self):
        event_id = SecurityEventLogger.log_security_violation(
            violation_type="Brute Force", details="Excessive login attempts detected."
        )
        self.assertIsNotNone(event_id)


class AddressValidationServiceTests(TestCase):
    def setUp(self):
        cache.clear()
        self.valid_data = {
            "street_address": "123 Test St",
            "city": "Test City",
            "postal_code": "12345",
            "country": "Test Country",
        }

    @patch("users.address_validation.AddressValidationService.validate_address")
    def test_address_validation(self, mock_validate_address):
        mock_validate_address.return_value = {"is_valid": True}
        from users.utils.address_validation import AddressValidationService

        validation_result = AddressValidationService.validate_address(self.valid_data)
        self.assertTrue(validation_result["is_valid"])
        mock_validate_address.assert_called_once_with(self.valid_data)


def test_validate_email_field_length(self):
    invalid_data = self.valid_data.copy()
    invalid_data["email"] = "a" * 300 + "@example.com"
    serializer = CustomRegisterSerializer(data=invalid_data)
    self.assertFalse(serializer.is_valid())
    self.assertIn("email", serializer.errors)


class CustomUserModelTests(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(email="test@example.com", password="secure123")
        self.assertEqual(user.email, "test@example.com")
        self.assertTrue(user.check_password("secure123"))

    def test_create_user_missing_required_fields(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(email=None, password="secure123")


from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

class UserAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="user@example.com", 
            password="password123"
        )
        self.user.is_verified = True
        self.user.save()

        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}'
        )

    def test_get_user_details(self):
        response = self.client.get("/api/users/me/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['user']['email'], self.user.email)

    def test_unauthenticated_access(self):
        self.client.credentials()
        response = self.client.get("/api/users/me/")
        self.assertEqual(response.status_code, 401)


class IntegrationTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    @patch("users.address_validation.AddressValidationService.validate_address")
    def test_register_user_and_retrieve_details(self, mock_validate_address):
        mock_validate_address.return_value = {"is_valid": True}
        register_data = {
            "email": "testuser@example.com",
            "password1": "Password123!",
            "password2": "Password123!",
            "full_name": "Test User",
            "accepted_terms": True,
            "phone_number": "+1234567890",
            "street_address": "123 Test St",
            "city": "Test City",
            "postal_code": "12345",
            "country": "GB",
        }
        response = self.client.post("/api/auth/registration/", data=register_data)
        self.assertEqual(response.status_code, 201)

        user = User.objects.get(email="testuser@example.com")
        user.is_verified = True
        user.save()

        login_data = {"email": "testuser@example.com", "password": "Password123!"}
        login_response = self.client.post("/api/auth/login/", data=login_data)
        self.assertEqual(login_response.status_code, 200)

        token = login_response.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        user_response = self.client.get("/api/users/me/")
        self.assertEqual(user_response.status_code, 200)
        self.assertEqual(user_response.data["user"]["email"], "testuser@example.com")
