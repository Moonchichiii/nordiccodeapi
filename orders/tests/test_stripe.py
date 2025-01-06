# orders/tests/test_stripe.py
import pytest
from unittest.mock import patch, MagicMock
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from orders.models import ProjectOrder, OrderPayment

User = get_user_model()

@pytest.mark.django_db
@patch("stripe.PaymentIntent.create")
def test_process_deposit(mock_stripe_create):
    """
    Test the /api/orders/{id}/process_deposit/ endpoint with a mocked Stripe create call.
    """
    user = User.objects.create_user(email="stripeuser@example.com", password="testpass")
    order = ProjectOrder.objects.create(
        user=user,
        project_type="StripeTest",
        description="Testing deposit",
        total_amount="1000.00",
    )  # deposit will default to 30% => $300
    
    mock_stripe_create.return_value = MagicMock(id="pi_mock123", client_secret="secret_abc")
    
    client = APIClient()
    client.login(email="stripeuser@example.com", password="testpass")
    
    url = reverse("orders-process-deposit", args=[order.id])
    response = client.post(url, {}, format="json")
    
    assert response.status_code == 200
    # Check that PaymentIntent was created with correct amount (300 * 100 = 30000)
    mock_stripe_create.assert_called_once_with(
        amount=30000,
        currency="usd",
        customer=user.stripe_customer_id,  # or None if not set
        metadata={"order_id": order.id, "payment_type": "deposit"}
    )
    
    # Verify an OrderPayment record was created
    payment = OrderPayment.objects.get(order=order)
    assert payment.stripe_payment_id == "pi_mock123"
    assert payment.status == "pending"


@pytest.mark.django_db
@patch("stripe.PaymentIntent.retrieve")
def test_confirm_deposit_success(mock_stripe_retrieve):
    """
    Test the /api/orders/{id}/confirm_deposit/ endpoint with a mocked PaymentIntent retrieve call.
    """
    user = User.objects.create_user(email="stripeconfirm@example.com", password="testpass")
    order = ProjectOrder.objects.create(
        user=user,
        project_type="StripeTestConfirm",
        description="Confirming deposit",
        total_amount="500.00",
    )
    # Create the pending payment
    payment = OrderPayment.objects.create(
        order=order,
        amount=order.deposit_amount,  # should be 150.00
        stripe_payment_id="pi_pending123",
        payment_type="deposit",
        status="pending",
    )
    
    mock_stripe_retrieve.return_value = MagicMock(status="succeeded")
    
    client = APIClient()
    client.login(email="stripeconfirm@example.com", password="testpass")

    url = reverse("orders-confirm-deposit", args=[order.id])
    response = client.post(url, {}, format="json")
    
    assert response.status_code == 200
    payment.refresh_from_db()
    order.refresh_from_db()
    # Payment should be completed
    assert payment.status == "completed"
    # Order status should be deposit_paid
    assert order.status == "deposit_paid"
    assert order.payment_status == "deposit_paid"
