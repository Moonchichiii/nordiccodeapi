from decimal import Decimal
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status

from backend.tests.base import BaseTestCase
from projects.models import Project, ProjectPackage

User = get_user_model()


class ProjectTests(BaseTestCase):
    """Test cases for the Project model."""

    def setUp(self):
        super().setUp()

        self.user = self.create_user(
            email="test@example.com", password="testpass123", full_name="Test User"
        )
        self.authenticate(self.user)

        self.package = ProjectPackage.objects.create(
            name="enterprise",
            base_price=Decimal("1000.00"),
            features=["Feature A", "Feature B"],
            tech_stack=["Python", "Django"],
            deliverables=["Deliverable A"],
            estimated_duration=30,
        )

        self.list_url = reverse("project-list")

        self.project_data = {
            "title": "Test Project",
            "description": "Test description",
            "status": "planning",
        }

    def create_test_project(self, **kwargs):
        """Helper to create a test project."""
        data = self.project_data.copy()
        data.update(kwargs)
        return Project.objects.create(user=self.user, **data)

    def test_create_project(self):
        """Test creating a project."""
        response = self.client.post(self.list_url, self.project_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        project = Project.objects.get(title=self.project_data["title"])
        self.assertEqual(project.user, self.user)

    def test_list_projects(self):
        """Test listing all projects."""
        project1 = self.create_test_project()
        project2 = self.create_test_project(title="Second Project")

        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertEqual(len(data), 2)
        self.assertIn(project1.title, [p["title"] for p in data])
        self.assertIn(project2.title, [p["title"] for p in data])

    def test_project_filtering(self):
        """Test filtering projects by status."""
        self.create_test_project(status="planning")
        self.create_test_project(status="completed", title="Completed Project")

        response = self.client.get(f"{self.list_url}?status=completed")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["title"], "Completed Project")

    def test_project_update_status(self):
        """Test updating the status of a project."""
        project = self.create_test_project()
        url = reverse("project-detail", args=[project.pk])

        response = self.client.patch(url, {"status": "in_progress"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        project.refresh_from_db()
        self.assertEqual(project.status, "in_progress")


class ProjectPackageTests(BaseTestCase):
    """Test cases for the ProjectPackage model."""

    def test_create_project_package(self):
        """Test creating a project package."""
        package = ProjectPackage.objects.create(
            name="premium",
            base_price=Decimal("1500.00"),
            features=["Feature X"],
            tech_stack=["Node.js", "Vue.js"],
            deliverables=["App with advanced features"],
            estimated_duration=45,
        )
        self.assertEqual(package.name, "premium")
        self.assertEqual(package.base_price, Decimal("1500.00"))

    def test_list_project_packages(self):
        """Test listing all project packages."""
        ProjectPackage.objects.create(
            name="enterprise",
            base_price=Decimal("2000.00"),
            features=["Feature A", "Feature B"],
            tech_stack=["React", "Django"],
            deliverables=["Complete App"],
            estimated_duration=30,
        )
        ProjectPackage.objects.create(
            name="basic",
            base_price=Decimal("500.00"),
            features=["Basic Feature"],
            tech_stack=["HTML", "CSS"],
            deliverables=["Static Website"],
            estimated_duration=10,
        )

        response = self.client.get(reverse("package-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data), 2)
