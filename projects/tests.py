"""Test module for Project model and related API endpoints.

This module contains test cases for the Project model's string representation
and API endpoints for listing and retrieving project details.
"""
import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from projects.models import Project


@pytest.mark.django_db
def test_project_model_str() -> None:
    """Test the string representation of Project model.

    Creates a test project and verifies its string representation.
    """
    project = Project.objects.create(
        title="My Portfolio",
        description="Just a test project",
        location="Remote",
        services="Design, Development",
        year="2023",
    )
    assert str(project) == "My Portfolio"


@pytest.mark.django_db
def test_list_projects_api() -> None:
    """Test the project listing API endpoint.

    Creates multiple test projects and verifies the list endpoint response.
    """
    client = APIClient()
    url = reverse("project-list")
    
    Project.objects.create(
        title="Project1",
        description="Desc1",
        location="Loc1",
        services="Serv1",
        year="2022",
    )
    Project.objects.create(
        title="Project2",
        description="Desc2",
        location="Loc2",
        services="Serv2",
        year="2023",
    )

    response = client.get(url)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2


@pytest.mark.django_db
def test_detail_project_api() -> None:
    """Test the project detail API endpoint.

    Creates a test project and verifies the detail endpoint response.
    """
    client = APIClient()
    project = Project.objects.create(
        title="DetailTest",
        description="DescTest",
        location="LocTest",
        services="ServTest",
        year="2023",
    )
    url = reverse("project-detail", args=[project.pk])
    response = client.get(url)

    assert response.status_code == 200
    resp_data = response.json()
    assert resp_data["title"] == "DetailTest"
