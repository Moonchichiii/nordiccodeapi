# users/tests/test_auth.py
import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
def test_user_registration():
    """Test user can sign up via /auth/registration/ endpoint."""
    client = APIClient()
    url = reverse("rest_register")  # Provided by dj_rest_auth
    data = {
        "email": "newuser@example.com",
        "password1": "StrongPass123",
        "password2": "StrongPass123",
        "accepted_terms": True,
    }
    response = client.post(url, data, format="json")
    assert response.status_code == 201 or response.status_code == 200
    # Verify user is created
    assert User.objects.filter(email="newuser@example.com").exists()


@pytest.mark.django_db
def test_login_logout_flow():
    """Test user can log in and log out."""
    user = User.objects.create_user(
        email="testlogin@example.com",
        password="pass123"
    )
    client = APIClient()
    
    # Login
    login_url = reverse("rest_login")
    response = client.post(
        login_url,
        {"email": "testlogin@example.com", "password": "pass123"},
        format="json",
    )
    assert response.status_code == 200
    
    # Check if token or session cookie returned
    # For JWT-based:
    #   assert "access_token" in response.data
    # Or for session-based:
    #   assert "sessionid" in response.cookies

    # Now test logout
    logout_url = reverse("rest_logout")
    response = client.post(logout_url, {}, format="json")
    assert response.status_code == 200


@pytest.mark.django_db
def test_fetch_profile(auth_client, test_user):
    """Test that we can fetch the user profile after logging in."""
    url = reverse("rest_user_details")  # Provided by dj_rest_auth
    response = auth_client.get(url)
    assert response.status_code == 200
    assert response.data["email"] == test_user.email


@pytest.mark.django_db
def test_delete_user_account(auth_client, test_user):
    """
    If your system allows user deletion via an endpoint,
    ensure the user is actually removed or set inactive.
    """
    # Example endpoint might be /auth/user/
    url = reverse("rest_user_details")
    response = auth_client.delete(url)
    # depends on your implementation
    assert response.status_code in [204, 200]
    assert not User.objects.filter(pk=test_user.pk).exists()
