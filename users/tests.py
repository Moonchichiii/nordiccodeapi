import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
def test_create_user():
    user = User.objects.create_user(email="normal@example.com", password="somepassword")
    assert user.email == "normal@example.com"
    assert user.check_password("somepassword")
    assert user.is_active is True


@pytest.mark.django_db
def test_create_superuser():
    superuser = User.objects.create_superuser(
        email="admin@example.com", password="adminpass"
    )
    assert superuser.is_staff is True
    assert superuser.is_superuser is True
