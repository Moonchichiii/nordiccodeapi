# projects/tests/test_integration.py
import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from projects.models import Project, Milestone

User = get_user_model()


@pytest.mark.django_db
def test_project_creation_and_milestones_flow(auth_client):
    """
    End-to-end style test:
    1) Create a project
    2) Add a requirement
    3) Add a milestone
    4) Complete the milestone
    5) Upload a deliverable
    """
    # 1) Create a project
    create_url = reverse("project-list")
    project_data = {
        "title": "TestProject",
        "description": "Project to test E2E",
        "location": "Remote",
        "services": "Design, Development",
        "year": "2024"
    }
    response = auth_client.post(create_url, project_data, format="json")
    assert response.status_code == 201
    project_id = response.data["id"]
    
    # 2) Add a requirement
    requirement_url = reverse("project-add-requirement", args=[project_id])
    req_data = {"requirement_type": "Front-end", "details": "React-based UI"}
    response = auth_client.post(requirement_url, req_data, format="json")
    assert response.status_code == 201
    assert "id" in response.data
    
    # 3) Add a milestone
    milestone_url = reverse("project-add-milestone", args=[project_id])
    mile_data = {
        "title": "Design Phase",
        "description": "Create initial wireframes",
        "due_date": "2025-01-31"
    }
    response = auth_client.post(milestone_url, mile_data, format="json")
    assert response.status_code == 201
    milestone_id = response.data["id"]
    
    # 4) Complete milestone
    complete_mile_url = reverse("project-complete-milestone", args=[project_id])
    response = auth_client.post(complete_mile_url, {"milestone_id": milestone_id}, format="json")
    assert response.status_code == 200
    milestone = Milestone.objects.get(pk=milestone_id)
    assert milestone.is_completed is True
    
    # 5) Upload deliverable
    upload_deliverable_url = reverse("project-upload-deliverable", args=[project_id])
    # If you want to test actual file upload, you can use Django's tempfile or BytesIO
    # Here we just send a placeholder JSON if the view can handle that
    deliverable_data = {"title": "Wireframe PDF", "version": "v1"}
    response = auth_client.post(upload_deliverable_url, deliverable_data, format="json")
    assert response.status_code == 201
    assert "id" in response.data


@pytest.mark.django_db
def test_only_owner_can_update_project(api_client, test_user):
    """Check that a user cannot update a project that doesn't belong to them."""
    # This test assumes you enforce ownership in the permission class or filter
    other_user = User.objects.create_user(email="other@example.com", password="pass123")
    
    project = Project.objects.create(
        title="OwnerProject",
        description="Should only be updatable by the owner",
        location="Remote",
        services="DevOps",
        year="2024"
    )
    # We'll simulate "owner" by setting a OneToOne or foreign key linking to test_user if your model does that
    # But if your project doesn't store a direct user, skip this or adapt your permission logic

    # Attempt update with non-owner
    api_client.login(email="other@example.com", password="pass123")
    update_url = reverse("project-detail", args=[project.pk])
    response = api_client.patch(update_url, {"description": "Hacked!"}, format="json")
    assert response.status_code in [403, 404]  # or whichever is returned if not permitted
