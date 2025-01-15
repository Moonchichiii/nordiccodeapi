"""
Test suite for user authentication, registration, token management,
password change, reset, and email confirmation flows.
Combines tests from both 'UserAuthTests' and 'PasswordFlowTests'.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from allauth.account.models import EmailAddress

User = get_user_model()


class UserAuthTests(TestCase):
    """
    Test cases for:
    - Registration (complete/minimal data)
    - Duplicate email registration
    - Login flows (verified vs unverified)
    - JWT token refresh with cookie-based auth
    - Case-insensitive login
    """

    def setUp(self):
        """Set up test client and common test data."""
        self.client = APIClient()

        # URLs
        self.register_url = reverse("rest_register")
        self.login_url = reverse("rest_login")
        self.logout_url = reverse("rest_logout")
        self.token_refresh_url = "/auth/token/refresh/"

        # Test user data
        self.user_data = {
            "email": "testuser@example.com",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
            "full_name": "Test User",
            "phone_number": "+1234567890",
            "street_address": "123 Test St",
            "city": "Test City",
            "state_or_region": "Test State",
            "postal_code": "12345",
            "country": "Test Country",
            "vat_number": "VAT123456",
            "accepted_terms": True,
            "marketing_consent": True,
        }

    def create_verified_user(self):
        """Helper method to create a verified user in the DB."""
        user = User.objects.create_user(
            email=self.user_data["email"], password=self.user_data["password1"]
        )
        EmailAddress.objects.create(
            user=user, email=user.email, verified=True, primary=True
        )
        return user

    def test_registration_with_complete_data(self):
        """Test user registration with all optional fields."""
        response = self.client.post(
            self.register_url, self.user_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user = User.objects.get(email=self.user_data["email"])
        for field in [
            "full_name",
            "phone_number",
            "street_address",
            "city",
            "state_or_region",
            "postal_code",
            "country",
            "vat_number",
        ]:
            self.assertEqual(getattr(user, field), self.user_data[field])
        self.assertTrue(user.accepted_terms)

    def test_registration_with_minimal_data(self):
        """Test user registration with only required fields."""
        minimal_data = {
            "email": "minimal@example.com",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
            "accepted_terms": True,
        }
        response = self.client.post(
            self.register_url, minimal_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user = User.objects.get(email=minimal_data["email"])
        self.assertTrue(user.accepted_terms)
        self.assertFalse(user.is_verified)

    def test_duplicate_email_registration(self):
        """Test registration with an existing email address."""
        User.objects.create_user(
            email=self.user_data["email"], password="password123"
        )
        response = self.client.post(
            self.register_url, self.user_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.json())

    def test_login_with_unverified_email(self):
        """Test login attempt with unverified email should fail."""
        user = User.objects.create_user(
            email=self.user_data["email"], password=self.user_data["password1"]
        )
        EmailAddress.objects.create(
            user=user, email=user.email, verified=False, primary=True
        )

        response = self.client.post(
            self.login_url,
            {"email": self.user_data["email"], "password": self.user_data["password1"]},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_with_verified_email(self):
        """Test successful login with verified email."""
        user = User.objects.create_user(
            email=self.user_data["email"], password=self.user_data["password1"]
        )
        EmailAddress.objects.create(
            user=user, email=user.email, verified=True, primary=True
        )
        user.is_verified = True
        user.save()

        response = self.client.post(
            self.login_url,
            {"email": self.user_data["email"], "password": self.user_data["password1"]},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_token_refresh(self):
        """Test refresh token functionality with cookie-based refresh."""
        self.create_verified_user()

        # Login => set refresh token in cookie
        login_resp = self.client.post(
            self.login_url,
            {"email": self.user_data["email"], "password": self.user_data["password1"]},
            format="json",
        )
        self.assertEqual(login_resp.status_code, status.HTTP_200_OK)

        # Extract refresh_token from cookies
        refresh_cookie = login_resp.cookies.get("refresh_token")
        self.assertIsNotNone(refresh_cookie)

        # Attach to client
        self.client.cookies["refresh_token"] = refresh_cookie.value

        # Request refresh with empty body => server looks at cookie
        refresh_resp = self.client.post(
            self.token_refresh_url, {}, format="json"
        )
        self.assertEqual(refresh_resp.status_code, status.HTTP_200_OK)
        self.assertIn("access", refresh_resp.data)

    def test_token_refresh_with_rotation(self):
        """Test refresh token rotation with cookie-based tokens."""
        self.create_verified_user()

        # Login => initial refresh
        login_resp = self.client.post(
            self.login_url,
            {"email": self.user_data["email"], "password": self.user_data["password1"]},
            format="json",
        )
        self.assertEqual(login_resp.status_code, status.HTTP_200_OK)

        initial_refresh_cookie = login_resp.cookies.get("refresh_token")
        self.assertIsNotNone(initial_refresh_cookie)
        initial_val = initial_refresh_cookie.value

        # 1st refresh
        self.client.cookies["refresh_token"] = initial_val
        first_resp = self.client.post(
            self.token_refresh_url, {}, format="json"
        )
        self.assertEqual(first_resp.status_code, status.HTTP_200_OK)

        rotated_cookie = first_resp.cookies.get("refresh_token")
        self.assertIsNotNone(rotated_cookie)
        self.assertNotEqual(rotated_cookie.value, initial_val)

        # 2nd refresh => use newly rotated token
        self.client.cookies["refresh_token"] = rotated_cookie.value
        second_resp = self.client.post(
            self.token_refresh_url, {}, format="json"
        )
        self.assertEqual(second_resp.status_code, status.HTTP_200_OK)
        self.assertIn("access", second_resp.data)

    def test_login_with_case_insensitive_email(self):
        """Test login with an uppercase email address."""
        self.create_verified_user()
        uppercase_email = self.user_data["email"].upper()
        resp = self.client.post(
            self.login_url,
            {"email": uppercase_email, "password": self.user_data["password1"]},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_invalid_token_refresh(self):
        """Test refresh token endpoint with invalid token."""
        resp = self.client.post(
            self.token_refresh_url, {"refresh": "invalid-token"}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
