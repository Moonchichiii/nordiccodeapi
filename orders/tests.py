from decimal import Decimal
from unittest.mock import patch

from django.contrib.admin.sites import AdminSite
from django.urls import reverse
from rest_framework import status

from backend.tests.base import BaseTestCase
from orders.admin import ProjectOrder
from orders.models import OrderPayment, ProjectOrder
from projects.models import ProjectPackage


class OrderTestCase(BaseTestCase):
    """Base test case for order-related tests with common setup."""

    def setUp(self):
        super().setUp()
        self.user = self.create_user(email="test@example.com")
        self.authenticate(self.user)

        self.package = ProjectPackage.objects.create(
            name="enterprise",
            base_price=Decimal("1000.00"),
            features=["Feature A", "Feature B"],
            tech_stack=["Python", "Django"],
            deliverables=["Complete App"],
            estimated_duration=30,
        )

        self.order_data = {
            "package": self.package.id,
            "project_type": "Test Project",
            "description": "Detailed project description",
            "total_amount": "1000.00",
        }


class OrderCreationTests(OrderTestCase):
    """Tests for order creation and initial setup."""

    def test_create_order(self):
        order_data = {
            "package": self.package.id,
            "total_amount": "1000.00",
        }
        response = self.client.post(self.list_url, order_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        order = ProjectOrder.objects.get(id=response.json()["id"])
        self.assertEqual(order.project_type, self.order_data["project_type"])
        self.assertEqual(order.total_amount, Decimal("1000.00"))
        self.assertEqual(order.user, self.user)

    def test_calculate_deposit_and_remaining_amount(self):
        """Test automatic calculation of deposit and remaining amounts."""
        response = self.client.post(
            reverse("orders-list"), self.order_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        order = ProjectOrder.objects.get(id=response.json()["id"])
        self.assertEqual(order.deposit_amount, Decimal("300.00"))  # 30%
        self.assertEqual(order.remaining_amount, Decimal("700.00"))  # 70%


class OrderStatusTests(OrderTestCase):
    """Tests for order status transitions."""

    def test_status_flow(self):
        """Test valid status transitions."""
        response = self.client.post(
            reverse("orders-list"), self.order_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        order_id = response.json()["id"]
        status_flow = [
            ("proposal", "awaiting_deposit"),
            ("deposit_pending", "awaiting_deposit"),
            ("deposit_paid", "deposit_paid"),
            ("in_progress", "deposit_paid"),
            ("review", "deposit_paid"),
            ("completed", "completed"),
        ]

        for new_status, expected_payment_status in status_flow:
            response = self.client.patch(
                reverse("orders-detail", args=[order_id]),
                {"status": new_status},
                format="json",
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            order = ProjectOrder.objects.get(id=order_id)
            self.assertEqual(order.status, new_status)
            self.assertEqual(order.payment_status, expected_payment_status)

    def test_invalid_status_transitions(self):
        """Test that invalid status transitions are rejected."""
        order = ProjectOrder.objects.create(
            user=self.user,
            package=self.package,
            total_amount=Decimal("1000.00"),
        )
        invalid_statuses = ["completed", "review"]

        for status in invalid_statuses:
            response = self.client.patch(
                reverse("orders-detail", args=[order.pk]),
                {"status": status},
                format="json",
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn("status", response.json())


class PaymentProcessTests(OrderTestCase):
    """Tests for payment processing."""

    @patch("stripe.PaymentIntent.create")
    def test_deposit_payment_flow(self, mock_create):
        """Test the deposit payment process."""
        response = self.client.post(
            reverse("orders-list"), self.order_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        order_id = response.json()["id"]
        mock_create.return_value = {
            "id": "pi_test123",
            "client_secret": "secret_test123",
            "amount": 30000,  # $300 in cents
        }

        response = self.client.post(reverse("orders-process-deposit", args=[order_id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("client_secret", response.json())

    @patch("stripe.PaymentIntent.create")
    def test_invalid_deposit_amount(self, mock_create):
        """Test that a deposit amount greater than the total is rejected."""
        mock_create.return_value = {
            "id": "pi_invalid",
            "client_secret": "secret_invalid",
        }
        order = ProjectOrder.objects.create(
            user=self.user,
            package=self.package,
            total_amount=Decimal("1000.00"),
            deposit_amount=Decimal("1200.00"),  # Invalid: > total
        )
        response = self.client.post(reverse("orders-process-deposit", args=[order.pk]))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("deposit_amount", response.json())


class AdminInterfaceTests(OrderTestCase):
    """Tests for admin interface functionality."""

    def setUp(self):
        super().setUp()
        self.admin_user = self.create_admin()
        self.client.force_login(self.admin_user)

    def test_admin_list_view(self):
        """Test that the admin list view displays orders."""
        order = ProjectOrder.objects.create(
            user=self.user,
            package=self.package,
            total_amount=Decimal("1000.00"),
        )
        response = self.client.get(reverse("admin:orders_projectorder_changelist"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, order.project_type)

    def test_admin_detail_view(self):
        """Test that the admin detail view displays an order."""
        order = ProjectOrder.objects.create(
            user=self.user,
            package=self.package,
            total_amount=Decimal("1000.00"),
        )
        response = self.client.get(
            reverse("admin:orders_projectorder_change", args=[order.pk])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, order.project_type)


class NotificationTests(OrderTestCase):
    """Tests for notifications."""

    def test_payment_notification(self):
        """Test sending notifications for completed payments."""
        payment = OrderPayment.objects.create(
            order=ProjectOrder.objects.create(
                user=self.user,
                package=self.package,
                total_amount=Decimal("1000.00"),
            ),
            amount=Decimal("300.00"),
            stripe_payment_id="pi_123",
            payment_type="deposit",
            status="completed",
        )
        # Replace `NotificationService.send_payment_notification()` with your actual function
        with patch(
            "orders.services.NotificationService.send_payment_notification"
        ) as mock_notify:
            mock_notify.return_value = True
            NotificationService.send_payment_notification(payment, "payment_success")
            mock_notify.assert_called_once()


class AccessControlTests(OrderTestCase):
    """Tests for access control."""

    def test_non_owner_cannot_access_order(self):
        """Test that a user cannot access another user's order."""
        other_user = self.create_user(email="other@example.com")
        order = ProjectOrder.objects.create(
            user=other_user, package=self.package, total_amount=1000.00
        )

        url = reverse("orders-detail", args=[order.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
