"""Test module for ProjectOrder functionality in the orders application."""

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from orders.models import ProjectOrder

User = get_user_model()


@pytest.mark.django_db
def test_project_order_str():
    """Test the string representation of ProjectOrder model.
    
    Creates a test user and project order, then verifies the string output format.
    """
    user = User.objects.create_user(
        email="orderuser@example.com",
        password="testpass"
    )
    order = ProjectOrder.objects.create(
        user=user,
        project_type="Simple Website",
        description="Some description",
        status="pending"
    )
    expected_str = f"Order #{order.pk} - Simple Website"
    assert str(order) == expected_str


@pytest.mark.django_db
def test_create_order_unauthenticated():
    """Test order creation with unauthenticated user.
    
    Verifies that unauthorized users cannot create orders.
    """
    client = APIClient()
    url = reverse("orders-list")
    data = {
        "project_type": "E-commerce",
        "description": "Need a store"
    }
    response = client.post(url, data, format='json')
    assert response.status_code == 401


@pytest.mark.django_db
def test_create_order_authenticated():
    """Test order creation with authenticated user.
    
    Verifies that authorized users can create orders with correct data.
    """
    user = User.objects.create_user(
        email="authuser@example.com",
        password="testpass"
    )
    client = APIClient()
    client.login(email="authuser@example.com", password="testpass")

    url = reverse("orders-list")
    data = {
        "project_type": "E-commerce",
        "description": "Need a store ASAP"
    }
    response = client.post(url, data, format='json')
    assert response.status_code == 201

    order = ProjectOrder.objects.get()
    assert order.project_type == "E-commerce"
    assert order.description == "Need a store ASAP"
    assert order.user == user
    assert order.status == "pending"
