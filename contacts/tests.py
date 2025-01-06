"""Test module for Contact API endpoints and model functionality.

This module contains test cases for the Contact model and its API endpoints,
including creation and listing of contacts.
"""
import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from contacts.models import Contact


@pytest.mark.django_db
def test_contact_model_str():
    """Test the string representation of the Contact model."""
    contact = Contact.objects.create(
        name="Alice",
        email="alice@example.com",
        message="Hello!"
    )
    assert str(contact) == "Alice - alice@example.com"


@pytest.mark.django_db
def test_create_contact_api():
    """Test the contact creation through API endpoint."""
    client = APIClient()
    url = reverse("contact-list")
    data = {
        "name": "Bob",
        "email": "bob@example.com",
        "message": "Test message"
    }
    response = client.post(url, data, format="json")

    assert response.status_code == 201
    assert Contact.objects.filter(email="bob@example.com").exists()


@pytest.mark.django_db
def test_list_contacts_api():
    """Test the listing of contacts through API endpoint."""
    client = APIClient()
    url = reverse("contact-list")
    Contact.objects.create(
        name="User1",
        email="u1@example.com",
        message="Hi 1"
    )
    Contact.objects.create(
        name="User2",
        email="u2@example.com",
        message="Hi 2"
    )

    response = client.get(url)
    data = response.json()

    assert response.status_code == 200
    assert len(data) >= 2
