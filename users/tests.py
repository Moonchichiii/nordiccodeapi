"""Test module for custom user model authentication functionality.

This module contains test cases for user creation and authentication,
including both regular users and superusers.
"""
import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
def test_create_user():
    """Test creation and authentication of a regular user.

    Verifies that a user can be created with an email and password,
    and that the authentication works correctly.
    """
    user = User.objects.create_user(
        email="normal@example.com",
        password="somepassword"
    )
    assert user.email == "normal@example.com"
    assert user.check_password("somepassword")
    assert user.is_active is True


@pytest.mark.django_db
def test_create_superuser():
    """Test creation and verification of a superuser.

    Ensures that a superuser is created with the correct staff
    and superuser permissions.
    """
    superuser = User.objects.create_superuser(
        email="admin@example.com",
        password="adminpass"
    )
    assert superuser.is_staff is True
    assert superuser.is_superuser is True
