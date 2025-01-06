import pytest
from django.urls import reverse, resolve
from backend.urls import urlpatterns

@pytest.mark.django_db
def test_url_resolves():
    """Example test to confirm certain URLs resolve to the correct view."""
    resolver = resolve("/auth/registration/")
    assert resolver is not None
    # You can also check resolver.view_name or similar.

def test_settings_are_loaded(settings):
    """Check critical environment variables or settings are set."""
    assert settings.SECRET_KEY is not None
    assert settings.STRIPE_SECRET_KEY is not None
