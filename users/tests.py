import re

from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

User = get_user_model()


class UserAuthTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse("rest_register")
        self.login_url = reverse("rest_login")
        self.logout_url = reverse("rest_logout")
        self.token_refresh_url = reverse("token_refresh")

        self.user_data = {
            "email": "testuser@example.com",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
            "full_name": "Test User",
            "phone_number": "123456789",
            "street_address": "123 Test St",
            "city": "Test City",
            "state_or_region": "Test State",
            "postal_code": "12345",
            "country": "Test Country",
            "vat_number": "VAT123456",
            "accepted_terms": True,
            "marketing_consent": True,
        }

    def test_registration_with_complete_data(self):
        response = self.client.post(self.register_url, self.user_data, format="json")
        self.assertEqual(response.status_code, 201)

        user = User.objects.get(email=self.user_data["email"])
        self.assertEqual(user.full_name, self.user_data["full_name"])
        self.assertEqual(user.phone_number, self.user_data["phone_number"])
        self.assertEqual(user.street_address, self.user_data["street_address"])
        self.assertEqual(user.city, self.user_data["city"])
        self.assertEqual(user.state_or_region, self.user_data["state_or_region"])
        self.assertEqual(user.postal_code, self.user_data["postal_code"])
        self.assertEqual(user.country, self.user_data["country"])
        self.assertEqual(user.vat_number, self.user_data["vat_number"])
        self.assertTrue(user.accepted_terms)

    def test_registration_with_minimal_data(self):
        minimal_data = {
            "email": "minimal@example.com",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
            "accepted_terms": True,
        }
        response = self.client.post(self.register_url, minimal_data, format="json")
        self.assertEqual(response.status_code, 201)

        user = User.objects.get(email=minimal_data["email"])
        self.assertIsNotNone(user)
        self.assertTrue(user.accepted_terms)

    def test_duplicate_email_registration(self):
        User.objects.create_user(email=self.user_data["email"], password="password123")
        response = self.client.post(self.register_url, self.user_data, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("email", response.json())

    def test_login_with_unverified_email(self):
        User.objects.create_user(
            email=self.user_data["email"], password=self.user_data["password1"]
        )
        login_data = {
            "email": self.user_data["email"],
            "password": self.user_data["password1"],
        }
        response = self.client.post(self.login_url, login_data, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("non_field_errors", response.json())

    def test_login_with_verified_email(self):
        user = User.objects.create_user(
            email=self.user_data["email"], password=self.user_data["password1"]
        )
        EmailAddress.objects.create(user=user, email=user.email, verified=True)
        login_data = {
            "email": self.user_data["email"],
            "password": self.user_data["password1"],
        }
        response = self.client.post(self.login_url, login_data, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.json())
        self.assertIn("refresh", response.json())

    def test_token_refresh(self):
        user = User.objects.create_user(
            email=self.user_data["email"], password=self.user_data["password1"]
        )
        EmailAddress.objects.create(user=user, email=user.email, verified=True)

        login_response = self.client.post(
            self.login_url,
            {"email": self.user_data["email"], "password": self.user_data["password1"]},
            format="json",
        )

        self.assertEqual(login_response.status_code, 200)
        refresh_token = login_response.json().get("refresh")
        self.assertIsNotNone(refresh_token)

        self.client.cookies["refresh_token"] = refresh_token

        response = self.client.post(self.token_refresh_url, {}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.json())


class EmailVerificationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse("rest_register")
        self.user_data = {
            "email": "testuser@example.com",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
            "accepted_terms": True,
        }

    def test_email_verification_flow(self):
        response = self.client.post(self.register_url, self.user_data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(mail.outbox), 1)

        email_body = mail.outbox[0].body
        confirmation_key = re.search(
            r"/confirm-email/(?P<key>[-:\w]+)/", email_body
        ).group("key")
        self.assertIsNotNone(confirmation_key)

        verification_url = reverse(
            "account_confirm_email", kwargs={"key": confirmation_key}
        )
        response = self.client.get(verification_url)
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(email=self.user_data["email"])
        self.assertTrue(EmailAddress.objects.filter(user=user, verified=True).exists())
