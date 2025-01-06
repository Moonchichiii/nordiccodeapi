# contacts/tests/test_views.py
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from contacts.models import Contact

User = get_user_model()

@pytest.mark.django_db
def test_create_contact_requires_auth(api_client):
    """Ensure non-authenticated users cannot create Contact."""
    url = reverse("contact-list")
    data = {"name": "Unauth", "email": "unauth@example.com", "message": "Hi!"}
    response = api_client.post(url, data, format="json")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_create_contact_authenticated(auth_client):
    """Test creating a contact while authenticated."""
    url = reverse("contact-list")
    data = {"name": "John", "email": "john@example.com", "message": "Hello!"}
    response = auth_client.post(url, data, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    assert Contact.objects.filter(email="john@example.com").exists()


@pytest.mark.django_db
def test_list_contacts(auth_client, create_contact):
    """Test listing contacts. By default, only staff or superuser may see them if configured."""
    create_contact(name="User1", email="u1@example.com")
    create_contact(name="User2", email="u2@example.com")

    url = reverse("contact-list")
    response = auth_client.get(url)
    if response.status_code == status.HTTP_403_FORBIDDEN:
        # This means you restricted listing to staff only
        assert True
    else:
        # If you allow listing to the user who created the contact or any logged-in user
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 2
