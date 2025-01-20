import json
import logging

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from .models import Project, ProjectPackage

User = get_user_model()
logger = logging.getLogger(__name__)


class ProjectPackageTests(APITestCase):
    def setUp(self):
        """Set up test data."""
        # Create admin user
        self.admin_user = User.objects.create_user(
            email="admin@example.com",
            password="password123",
            full_name="Admin User",
            phone_number="1234567890",
            street_address="123 Main St",
            city="Anytown",
            state_or_region="State",
            postal_code="12345",
            country="Country",
            vat_number="VAT123456",
            accepted_terms=True,
            marketing_consent=True,
            is_verified=True,
            is_staff=True,
            is_active=True,
            is_superuser=True,
        )

        # Create regular user
        self.regular_user = User.objects.create_user(
            email="user@example.com",
            password="password123",
            full_name="Regular User",
            phone_number="0987654321",
            street_address="456 Side St",
            city="Othertown",
            state_or_region="State",
            postal_code="54321",
            country="Country",
            vat_number="VAT654321",
            accepted_terms=True,
            marketing_consent=True,
            is_verified=True,
            is_active=True,
        )

        self.client = APIClient()
        self.packages_list_url = reverse("projects:package-list")

    def test_create_project_package_admin(self):
        """Test admin can create package."""
        self.client.force_authenticate(user=self.admin_user)
        data = {
            "name": "enterprise",
            "base_price": "2000.00",
            "features": {"feature1": "Advanced Analytics"},
            "tech_stack": ["Python", "Django"],
            "deliverables": ["Complete App"],
            "estimated_duration": 60,
            "maintenance_period": 120,
            "sla_response_time": 12,
        }
        response = self.client.post(self.packages_list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ProjectPackage.objects.count(), 1)
        self.assertEqual(ProjectPackage.objects.get().name, "enterprise")

    def test_create_project_package_regular_user(self):
        """Test regular user cannot create package."""
        self.client.force_authenticate(user=self.regular_user)
        data = {
            "name": "enterprise",
            "base_price": "2000.00",
            "features": {"feature1": "Advanced Analytics"},
            "tech_stack": ["Python", "Django"],
            "deliverables": ["Complete App"],
            "estimated_duration": 60,
            "maintenance_period": 120,
            "sla_response_time": 12,
        }
        response = self.client.post(self.packages_list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(ProjectPackage.objects.count(), 0)

    def test_invalid_package_data(self):
        """Test validation of invalid package data."""
        self.client.force_authenticate(user=self.admin_user)
        data = {
            "name": "enterprise",
            "base_price": "-2000.00",  # Invalid negative price
            "features": {"feature1": "Advanced Analytics"},
            "tech_stack": ["Python", "Django"],
            "deliverables": ["Complete App"],
            "estimated_duration": -60,  # Invalid negative duration
            "maintenance_period": 120,
            "sla_response_time": 12,
        }
        response = self.client.post(self.packages_list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("base_price", response.data)
        self.assertIn("estimated_duration", response.data)


class ProjectTests(APITestCase):
    def setUp(self):
        """Set up test data."""
        # Create users
        self.user = User.objects.create_user(
            email="test@example.com",
            password="password123",
            full_name="Test User",
            phone_number="1234567890",
            street_address="123 Main St",
            city="Anytown",
            state_or_region="State",
            postal_code="12345",
            country="Country",
            vat_number="VAT123456",
            accepted_terms=True,
            marketing_consent=True,
            is_verified=True,
            is_active=True,
        )

        self.staff_user = User.objects.create_user(
            email="staff@example.com",
            password="password123",
            full_name="Staff User",
            is_staff=True,
            is_active=True,
        )

        self.client = APIClient()
        self.projects_list_url = reverse("projects:project-list")

        # Create test package
        self.package = ProjectPackage.objects.create(
            name="enterprise",
            base_price=1000.00,
            features={"feature1": "Basic Analytics"},
            tech_stack=["Django"],
            deliverables=["Source Code"],
            estimated_duration=30,
            maintenance_period=60,
            sla_response_time=24,
        )

        # Create test file
        self.test_file = SimpleUploadedFile(
            "test_doc.pdf", b"test content", content_type="application/pdf"
        )

    def test_create_project_authenticated(self):
        """Test creating project while authenticated."""
        self.client.force_authenticate(user=self.user)
        data = {
            "title": "Test Project",
            "description": "Test Description",
            "status": "planning",
            "package": self.package.id,
            "client_specifications": self.test_file,
        }
        response = self.client.post(self.projects_list_url, data, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Project.objects.count(), 1)
        project = Project.objects.get()
        self.assertEqual(project.title, "Test Project")
        self.assertEqual(project.status, "planning")
        self.assertEqual(project.user, self.user)

    def test_create_project_invalid_status(self):
        """Test creating project with invalid status."""
        self.client.force_authenticate(user=self.user)
        data = {
            "title": "Test Project",
            "description": "Test Description",
            "status": "invalid_status",
            "package": self.package.id,
        }
        response = self.client.post(self.projects_list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("status", response.data)

    def test_update_project_status_flow(self):
        """Test project status transitions."""
        self.client.force_authenticate(user=self.user)
        project = Project.objects.create(
            title="Status Test Project",
            description="Testing status flow",
            status="planning",
            user=self.user,
            package=self.package,
        )

        url = reverse("projects:project-detail", kwargs={"pk": project.id})

        # Planning -> In Progress
        response = self.client.patch(url, {"status": "in_progress"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        project.refresh_from_db()
        self.assertEqual(project.status, "in_progress")

        # In Progress -> Completed (Without assigning staff)
        response = self.client.patch(url, {"status": "completed"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("status", response.data)
        self.assertIn(
            "Cannot mark as completed without assigned staff", response.data["status"]
        )

        # Assign staff
        project.assigned_staff.add(self.staff_user)

        # In Progress -> Completed (With assigned staff)
        response = self.client.patch(url, {"status": "completed"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        project.refresh_from_db()
        self.assertEqual(project.status, "completed")

    def test_staff_assignment(self):
        """Test assigning staff to project."""
        self.client.force_authenticate(user=self.user)
        project = Project.objects.create(
            title="Staff Test Project",
            description="Testing staff assignment",
            status="planning",
            user=self.user,
            package=self.package,
        )

        url = reverse("projects:project-detail", kwargs={"pk": project.id})
        response = self.client.patch(
            url, {"assigned_staff": [self.staff_user.id]}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        project.refresh_from_db()
        self.assertTrue(self.staff_user in project.assigned_staff.all())
