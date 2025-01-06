# orders/tests/test_commission.py
import pytest
from django.utils import timezone
from django.contrib.auth import get_user_model
from orders.models import ProjectOrder

User = get_user_model()

@pytest.mark.django_db
def test_commission_process():
    """Test that process_commission() sets commission_status='paid' and commission_paid_at."""
    user = User.objects.create_user(email="commission@example.com", password="pass123")
    order = ProjectOrder.objects.create(
        user=user,
        project_type="Commission Test",
        description="Testing commissions",
        total_amount="1000.00",
        status="deposit_paid",  # Must be deposit_paid for process_commission
    )
    assert order.commission_status == "pending"
    assert order.commission_paid_at is None
    
    # Now process commission
    order.process_commission()
    order.refresh_from_db()
    
    assert order.commission_status == "paid"
    assert order.commission_paid_at is not None
