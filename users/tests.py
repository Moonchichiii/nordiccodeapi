"""Test module for user models."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from unittest.mock import patch, Mock
from django.core.cache import cache
from django.core.exceptions import ValidationError
import uuid
import requests

from users.serializers import (
    CustomLoginSerializer,
    CustomRegisterSerializer,
    CustomUserDetailsSerializer,
)

from users.services import AddressService, EmailService, SecurityService, TokenService

from allauth.account.models import EmailAddress, EmailConfirmation
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()


class BaseTestCase(TestCase):
    """Base test case with common tear down logic."""
    
    def tearDown(self) -> None:
        """Clean up after each test."""
        cache.clear()
        User.objects.all().delete()
        EmailAddress.objects.all().delete()
        EmailConfirmation.objects.all().delete()

class SecurityServiceTests(BaseTestCase):
    def tearDown(self) -> None:
        """Clean up after security tests."""
        super().tearDown()  
        cache.delete(f"login_attempts_{self.email}")
        cache.delete(f"login_attempts_{self.ip_address}")

class CustomUserModelTests(TestCase):
    """Tests for CustomUser model."""

    def setUp(self) -> None:
        self.user_data = {
            "email": "test@example.com",
            "password": "StrongPass123!",
            "full_name": "Test User",
            "phone_number": "+1234567890",
            "street_address": "123 Test St",
            "city": "Test City",
            "postal_code": "12345",
            "country": "GB",
            "accepted_terms": True
        }

    def test_create_user(self) -> None:
        """Test creating a normal user."""
        user = User.objects.create_user(
            email=self.user_data["email"],
            password=self.user_data["password"],
            full_name=self.user_data["full_name"],
            phone_number=self.user_data["phone_number"]
        )
        self.assertEqual(user.email, self.user_data["email"])
        self.assertTrue(user.check_password(self.user_data["password"]))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_verified)

    def test_create_superuser(self) -> None:
        """Test creating a superuser."""
        user = User.objects.create_superuser(**self.user_data)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_verified)

    def test_user_str_representation(self) -> None:
        """Test string representation of user."""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(str(user), self.user_data["email"])

    def test_get_full_name(self) -> None:
        """Test get_full_name method."""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.get_full_name(), self.user_data["full_name"])

    def test_get_short_name(self) -> None:
        """Test get_short_name method."""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.get_short_name(), "Test")

"""Test module for user serializers."""

class CustomRegisterSerializerTests(TestCase):
    """Tests for CustomRegisterSerializer."""

    def setUp(self) -> None:
        cache.clear()
        self.valid_data = {
            "email": "newuser@example.com",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
            "full_name": "Test User",
            "phone_number": "+1234567890",
            "street_address": "123 Test St",
            "city": "Test City",
            "postal_code": "12345",
            "country": "GB",
            "accepted_terms": True,
            "marketing_consent": False
        }

    @patch('users.services.AddressService.validate_address')
    def test_valid_registration(self, mock_validate_address) -> None:
        """Test registration with valid data."""
        mock_validate_address.return_value = {"is_valid": True}
        serializer = CustomRegisterSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save(None)  # None for request as it's not used
        self.assertEqual(user.email, self.valid_data["email"])
        self.assertEqual(user.full_name, self.valid_data["full_name"])
        self.assertEqual(user.phone_number, self.valid_data["phone_number"])

    def test_password_validation(self) -> None:
        """Test password validation."""
        # Test password mismatch
        data = self.valid_data.copy()
        data["password2"] = "DifferentPass123!"
        serializer = CustomRegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("password2", serializer.errors)

        # Test too short password
        data = self.valid_data.copy()
        data["password1"] = data["password2"] = "short"
        serializer = CustomRegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_required_fields(self) -> None:
        """Test required fields validation."""
        required_fields = [
            "email", "password1", "password2", "full_name",
            "phone_number", "street_address", "city",
            "postal_code", "country", "accepted_terms"
        ]
        for field in required_fields:
            data = self.valid_data.copy()
            data.pop(field)
            serializer = CustomRegisterSerializer(data=data)
            self.assertFalse(serializer.is_valid())
            self.assertIn(field, serializer.errors)

    def test_field_validations(self) -> None:
        """Test individual field validations."""
        # Test invalid email
        data = self.valid_data.copy()
        data["email"] = "invalid-email"
        serializer = CustomRegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)

        # Test invalid phone number
        data = self.valid_data.copy()
        data["phone_number"] = "123"
        serializer = CustomRegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("phone_number", serializer.errors)

        # Test invalid full name
        data = self.valid_data.copy()
        data["full_name"] = "a"  # Too short
        serializer = CustomRegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("full_name", serializer.errors)

class CustomLoginSerializerTests(TestCase):
    """Tests for CustomLoginSerializer."""

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email="test@example.com",
            password="StrongPass123!",
            full_name="Test User",
            phone_number="+1234567890",
            is_verified=True
        )
        self.valid_data = {
            "email": "test@example.com",
            "password": "StrongPass123!"
        }

    def test_valid_login(self) -> None:
        """Test login with valid credentials."""
        serializer = CustomLoginSerializer(
            data=self.valid_data,
            context={"request": None}
        )
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["user"], self.user)

    def test_unverified_user(self) -> None:
        """Test login with unverified email."""
        self.user.is_verified = False
        self.user.save()
        serializer = CustomLoginSerializer(
            data=self.valid_data,
            context={"request": None}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("verify your email", str(serializer.errors["non_field_errors"]))

    def test_invalid_credentials(self) -> None:
        """Test login with invalid credentials."""
        # Test wrong password
        data = self.valid_data.copy()
        data["password"] = "WrongPass123!"
        serializer = CustomLoginSerializer(data=data, context={"request": None})
        self.assertFalse(serializer.is_valid())
        self.assertIn("Invalid credentials", str(serializer.errors["non_field_errors"]))

        # Test non-existent email
        data = self.valid_data.copy()
        data["email"] = "nonexistent@example.com"
        serializer = CustomLoginSerializer(data=data, context={"request": None})
        self.assertFalse(serializer.is_valid())

class CustomUserDetailsSerializerTests(TestCase):
    """Tests for CustomUserDetailsSerializer."""

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email="test@example.com",
            password="StrongPass123!",
            full_name="Test User",
            phone_number="+1234567890",
            street_address="123 Test St",
            city="Test City",
            postal_code="12345",
            country="GB",
            state_or_region="Test Region",
            vat_number="GB123456789",
            is_verified=True,
            accepted_terms=True,
            marketing_consent=False
        )
        self.serializer = CustomUserDetailsSerializer(instance=self.user)

    def test_serializer_fields(self) -> None:
        """Test if serializer includes all expected fields."""
        data = self.serializer.data
        expected_fields = {
            "email",
            "full_name",
            "phone_number",
            "street_address",
            "city",
            "state_or_region",
            "postal_code",
            "country",
            "vat_number",
            "accepted_terms",
            "marketing_consent",
            "is_verified"
        }
        self.assertEqual(set(data.keys()), expected_fields)
        
        # Verify field values
        self.assertEqual(data["email"], self.user.email)
        self.assertEqual(data["full_name"], self.user.full_name)
        self.assertEqual(data["phone_number"], self.user.phone_number)
        self.assertEqual(data["street_address"], self.user.street_address)
        self.assertEqual(data["city"], self.user.city)
        self.assertEqual(data["postal_code"], self.user.postal_code)
        self.assertEqual(data["country"], self.user.country)
        self.assertEqual(data["state_or_region"], self.user.state_or_region)
        self.assertEqual(data["vat_number"], self.user.vat_number)
        self.assertEqual(data["is_verified"], self.user.is_verified)
        self.assertEqual(data["accepted_terms"], self.user.accepted_terms)
        self.assertEqual(data["marketing_consent"], self.user.marketing_consent)

    @patch('users.services.AddressService.validate_address')
    def test_update_user_details(self, mock_validate_address) -> None:
        """Test updating user details."""
        mock_validate_address.return_value = {"is_valid": True}
        
        update_data = {
            "full_name": "Updated User",
            "phone_number": "+9876543210",
            "street_address": "456 New St",
            "city": "New City",
            "postal_code": "54321",
            "country": "FR",
            "state_or_region": "New Region",
            "vat_number": "FR987654321",
            "marketing_consent": True
        }
        
        serializer = CustomUserDetailsSerializer(
            instance=self.user,
            data=update_data,
            partial=True
        )
        
        self.assertTrue(serializer.is_valid())
        updated_user = serializer.save()
        
        # Verify updated fields
        for field, value in update_data.items():
            self.assertEqual(getattr(updated_user, field), value)

    def test_readonly_fields(self) -> None:
        """Test readonly fields cannot be updated."""
        readonly_updates = {
            "email": "newemail@example.com",
            "is_verified": False,
            "accepted_terms": False
        }
        
        serializer = CustomUserDetailsSerializer(
            instance=self.user,
            data=readonly_updates,
            partial=True
        )
        
        self.assertTrue(serializer.is_valid())
        updated_user = serializer.save()
        
        # Verify readonly fields remain unchanged
        self.assertEqual(updated_user.email, self.user.email)
        self.assertEqual(updated_user.is_verified, self.user.is_verified)
        self.assertEqual(updated_user.accepted_terms, self.user.accepted_terms)

    @patch('users.services.AddressService.validate_address')
    def test_invalid_address_update(self, mock_validate_address) -> None:
        """Test updating with invalid address."""
        mock_validate_address.return_value = {"is_valid": False}
        
        update_data = {
            "street_address": "Invalid St",
            "city": "Invalid City",
            "postal_code": "Invalid",
            "country": "XX"
        }
        
        serializer = CustomUserDetailsSerializer(
            instance=self.user,
            data=update_data,
            partial=True
        )
        
        self.assertFalse(serializer.is_valid())
        self.assertIn("address", serializer.errors)

    def test_phone_number_validation(self) -> None:
        """Test phone number validation."""
        invalid_phone_numbers = [
            "123",  # Too short
            "abcdefghijk",  # Non-numeric
            "++1234567890",  # Invalid format
            "+123"  # Too short with prefix
        ]
        
        for phone_number in invalid_phone_numbers:
            serializer = CustomUserDetailsSerializer(
                instance=self.user,
                data={"phone_number": phone_number},
                partial=True
            )
            self.assertFalse(serializer.is_valid())
            self.assertIn("phone_number", serializer.errors)

    def test_full_name_validation(self) -> None:
        """Test full name validation."""
        invalid_names = [
            "a",  # Too short
            "123",  # Numbers
            "@#$",  # Special characters
            " " * 5  # Only spaces
        ]
        
        for name in invalid_names:
            serializer = CustomUserDetailsSerializer(
                instance=self.user,
                data={"full_name": name},
                partial=True
            )
            self.assertFalse(serializer.is_valid())
            self.assertIn("full_name", serializer.errors)

    def test_partial_update(self) -> None:
        """Test partial update with single field."""
        serializer = CustomUserDetailsSerializer(
            instance=self.user,
            data={"marketing_consent": True},
            partial=True
        )
        
        self.assertTrue(serializer.is_valid())
        updated_user = serializer.save()
        self.assertTrue(updated_user.marketing_consent)
        self.assertEqual(updated_user.full_name, self.user.full_name)
        self.assertEqual(updated_user.phone_number, self.user.phone_number)

"""Test module for user services."""
class TokenServiceTests(TestCase):
    """Tests for TokenService."""

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email="token@example.com",
            password="StrongPass123!",
            full_name="Test User",
            phone_number="+1234567890"
        )

    def test_create_token_payload(self) -> None:
        """Test token payload creation."""
        token_type = "access"
        token_id = str(uuid.uuid4())
        payload = TokenService._create_token_payload(self.user, token_type, token_id)
        
        self.assertEqual(payload['token_type'], token_type)
        self.assertEqual(payload['jti'], token_id)
        self.assertEqual(payload['user_id'], str(self.user.id))
        self.assertEqual(payload['email'], self.user.email)
        self.assertEqual(payload['is_verified'], self.user.is_verified)
        self.assertIn('iat', payload)

    def test_get_tokens_for_user(self) -> None:
        """Test generating refresh and access tokens."""
        tokens = TokenService.get_tokens_for_user(self.user)
        
        self.assertIn('refresh', tokens)
        self.assertIn('access', tokens)
        self.assertTrue(isinstance(tokens['refresh'], str))
        self.assertTrue(isinstance(tokens['access'], str))

    @patch('rest_framework_simplejwt.tokens.RefreshToken.objects.filter')
    def test_revoke_user_tokens(self, mock_filter) -> None:
        """Test revoking user tokens."""
        mock_delete = Mock()
        mock_filter.return_value = Mock(delete=mock_delete)
        TokenService.revoke_user_tokens(self.user)
        mock_filter.assert_called_once_with(user=self.user)
        mock_delete.assert_called_once()

class SecurityServiceTests(TestCase):
    """Tests for SecurityService."""

    def setUp(self) -> None:
        cache.clear()
        self.email = "test@example.com"
        self.ip_address = "127.0.0.1"
        self.user = User.objects.create_user(
            email=self.email,
            password="StrongPass123!",
            full_name="Test User",
            phone_number="+1234567890"
        )

    def test_check_login_attempts_success(self) -> None:
        """Test successful login attempts check."""
        for _ in range(SecurityService.MAX_ATTEMPTS - 1):
            result = SecurityService.check_login_attempts(self.email)
            self.assertTrue(result)

    def test_check_login_attempts_lockout(self) -> None:
        """Test lockout after max attempts."""
        for _ in range(SecurityService.MAX_ATTEMPTS):
            SecurityService.check_login_attempts(self.email)
        result = SecurityService.check_login_attempts(self.email)
        self.assertFalse(result)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)

    def test_check_login_attempts_ip_based(self) -> None:
        """Test IP-based login attempts."""
        for _ in range(SecurityService.MAX_ATTEMPTS - 1):
            result = SecurityService.check_login_attempts(None, self.ip_address)
            self.assertTrue(result)
        result = SecurityService.check_login_attempts(None, self.ip_address)
        self.assertFalse(result)

    def test_reset_attempts(self) -> None:
        """Test resetting login attempts."""
        SecurityService.check_login_attempts(self.email)
        SecurityService.reset_attempts(self.email)
        key = f"login_attempts_{self.email}"
        self.assertIsNone(cache.get(key))

    def test_unlock_account(self) -> None:
        """Test unlocking a user account."""
        self.user.is_active = False
        self.user.save()
        result = SecurityService.unlock_account(self.email)
        self.assertTrue(result)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)

    def test_log_security_event(self) -> None:
        """Test security event logging."""
        event_data = {
            'user_id': str(self.user.id),
            'action': 'login_attempt'
        }
        event_id = SecurityService.log_security_event('login_attempt', event_data)
        self.assertTrue(isinstance(event_id, str))
        self.assertTrue(uuid.UUID(event_id))

class AddressServiceTests(TestCase):
    """Tests for AddressService."""

    def setUp(self) -> None:
        self.valid_address = {
            "street_address": "123 Test St",
            "postal_code": "12345",
            "city": "Test City",
            "country": "UK"
        }

    def test_validate_country_success(self) -> None:
        """Test successful country validation."""
        for country in AddressService.ALLOWED_EU_COUNTRIES:
            self.assertTrue(AddressService.validate_country(country))

    def test_validate_country_failure(self) -> None:
        """Test country validation failure."""
        with self.assertRaises(ValidationError):
            AddressService.validate_country("US")

    def test_country_name_to_iso(self) -> None:
        """Test country name to ISO code conversion."""
        self.assertEqual(
            AddressService.validate_country("United Kingdom"),
            True
        )

    @patch('requests.post')
    def test_validate_address_success(self, mock_post) -> None:
        """Test successful address validation."""
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"normalized_address": {}}
        
        result = AddressService.validate_address(
            self.valid_address["street_address"],
            self.valid_address["postal_code"],
            self.valid_address["city"],
            self.valid_address["country"]
        )
        self.assertTrue(result["is_valid"])

    @patch('requests.post')
    def test_validate_address_service_error(self, mock_post) -> None:
        """Test address validation with service error."""
        mock_post.side_effect = requests.RequestException()
        result = AddressService.validate_address(
            self.valid_address["street_address"],
            self.valid_address["postal_code"],
            self.valid_address["city"],
            self.valid_address["country"]
        )
        self.assertFalse(result["is_valid"])
        self.assertEqual(
            result["error"],
            "Address validation service unavailable"
        )

class EmailServiceTests(TestCase):
    """Tests for EmailService."""

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email="test@example.com",
            password="StrongPass123!",
            full_name="Test User",
            phone_number="+1234567890"
        )
        self.activation_link = "http://testserver/activate/token123"

    @patch('django.core.mail.send_mail')
    @patch('users.services.SecurityService.log_security_event')
    def test_send_activation_email(self, mock_log_event, mock_send_mail) -> None:
        """Test sending activation email."""
        EmailService.send_activation_email(self.user, self.activation_link)
        
        mock_send_mail.assert_called_once()
        mock_log_event.assert_called_once_with(
            'email_sent',
            {'email': self.user.email, 'type': 'activation'}
        )

        call_args = mock_send_mail.call_args[0]
        self.assertEqual(call_args[0], "Verify your account")
        self.assertIn(self.activation_link, call_args[1])
        self.assertIn(self.user.full_name, call_args[1])

"""Test module for user views."""
class LoginViewTests(TestCase):
    """Tests for LoginView."""

    def setUp(self) -> None:
        cache.clear()
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="testuser@example.com",
            password="StrongPass123!",
            full_name="Test User",
            phone_number="+1234567890",
            is_verified=True
        )
        self.login_url = "/api/auth/login/"
        self.login_data = {
            "email": "testuser@example.com",
            "password": "StrongPass123!"
        }

    def test_successful_login(self) -> None:
        """Test successful login."""
        response = self.client.post(self.login_url, self.login_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("tokens", response.data)
        self.assertIn("access", response.data["tokens"])
        self.assertIn("refresh", response.data["tokens"])

    def test_login_unverified_email(self) -> None:
        """Test login attempt with unverified email."""
        self.user.is_verified = False
        self.user.save()
        response = self.client.post(self.login_url, self.login_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("verify your email", str(response.data["non_field_errors"]))

    def test_login_wrong_password(self) -> None:
        """Test login attempt with wrong password."""
        data = self.login_data.copy()
        data["password"] = "WrongPass123!"
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid credentials", str(response.data["non_field_errors"]))

    @patch('users.services.SecurityService.check_login_attempts')
    def test_login_account_locked(self, mock_check_attempts) -> None:
        """Test login attempt when account is locked."""
        mock_check_attempts.return_value = False
        response = self.client.post(self.login_url, self.login_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("Account locked", str(response.data["detail"]))

class EmailVerificationTests(TestCase):
    """Tests for email verification functionality."""

    def setUp(self) -> None:
        cache.clear()
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="testuser@example.com",
            password="StrongPass123!",
            full_name="Test User",
            phone_number="+1234567890"
        )
        self.email_address = EmailAddress.objects.create(
            user=self.user,
            email=self.user.email,
            primary=True,
            verified=False
        )
        self.confirmation = EmailConfirmation.create(self.email_address)
        self.verification_url = f"/api/users/verify-email/{self.confirmation.key}/"

    def test_successful_verification(self) -> None:
        """Test successful email verification."""
        response = self.client.get(self.verification_url)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_verified)
        self.assertIn("email-verified", response.url)

    def test_invalid_key(self) -> None:
        """Test verification with invalid key."""
        response = self.client.get("/api/users/verify-email/invalid-key/")
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertIn("email-verification-failed", response.url)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_verified)

    @patch('allauth.account.models.EmailConfirmation.has_expired')
    def test_expired_key(self, mock_has_expired) -> None:
        """Test verification with expired key."""
        mock_has_expired.return_value = True
        response = self.client.get(self.verification_url)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertIn("expired", response.url)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_verified)

class UserDetailsViewTests(TestCase):
    """Tests for UserDetailsView."""

    def setUp(self) -> None:
        cache.clear()
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="testuser@example.com",
            password="StrongPass123!",
            full_name="Test User",
            phone_number="+1234567890",
            street_address="123 Test St",
            city="Test City",
            postal_code="12345",
            country="GB",
            is_verified=True
        )
        self.client.force_authenticate(user=self.user)
        self.me_url = "/api/users/me/"

    def test_get_user_details(self) -> None:
        """Test retrieving user details."""
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], self.user.email)
        self.assertEqual(response.data["full_name"], self.user.full_name)
        self.assertEqual(response.data["phone_number"], self.user.phone_number)

    @patch('users.services.AddressService.validate_address')
    def test_update_user_details(self, mock_validate_address) -> None:
        """Test updating user details."""
        mock_validate_address.return_value = {"is_valid": True}
        new_data = {
            "full_name": "Updated Name",
            "phone_number": "+9876543210",
            "street_address": "456 New St",
            "city": "New City"
        }
        response = self.client.patch(self.me_url, new_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.full_name, new_data["full_name"])
        self.assertEqual(self.user.phone_number, new_data["phone_number"])
        self.assertEqual(self.user.street_address, new_data["street_address"])

    def test_update_readonly_fields(self) -> None:
        """Test attempting to update readonly fields."""
        response = self.client.patch(self.me_url, {
            "email": "newemail@example.com",
            "is_verified": False,
            "accepted_terms": False
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "testuser@example.com")
        self.assertTrue(self.user.is_verified)

    def test_unauthorized_access(self) -> None:
        """Test access without authentication."""
        self.client.force_authenticate(user=None)
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch('users.services.AddressService.validate_address')
    def test_invalid_address_update(self, mock_validate_address) -> None:
        """Test updating with invalid address."""
        mock_validate_address.return_value = {"is_valid": False}
        response = self.client.patch(self.me_url, {
            "street_address": "Invalid St",
            "city": "Invalid City"
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("address", response.data)