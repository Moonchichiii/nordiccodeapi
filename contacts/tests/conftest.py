# contacts/tests/conftest.py
import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from contacts.models import Contact
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.fixture
def api_client():
    """Returns an instance of DRF's APIClient for making requests."""
    return APIClient()

@pytest.fixture
def test_user(db):
    """Creates and returns a basic User for authentication tests."""
    user = User.objects.create_user(
        email="testuser@example.com", password="testpass"
    )
    return user

@pytest.fixture
def auth_client(api_client, test_user):
    """Logs in the test_user and returns an authenticated client."""
    api_client.login(email="testuser@example.com", password="testpass")
    return api_client

@pytest.fixture
def create_contact(db):
    """A fixture that creates a Contact instance."""
    def _create_contact(**kwargs):
        data = {
            "name": "Sample Name",
            "email": "contact@example.com",
            "message": "Hello from fixture!"
        }
        data.update(kwargs)
        return Contact.objects.create(**data)
    return _create_contact
