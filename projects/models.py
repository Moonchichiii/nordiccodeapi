"""Models for managing project information in the Nordic Code API.

This module defines the database models for storing and managing project-related data,
including details like title, description, location, and other project attributes.
"""

from django.db import models


class Project(models.Model):
    """Model representing a project entity.

    Attributes:
        title (str): The name of the project (max 200 characters)
        description (str): Detailed description of the project
        location (str): Geographic location of the project (max 100 characters)
        services (str): Services provided in the project (max 200 characters)
        year (str): Year of project completion (4 characters)
        image (ImageField): Project image file (optional)
        category (str): Project category or type (max 100 characters)
        link (str): Internal reference link (max 200 characters)
        external_link (URL): External project URL (optional)
        featured (bool): Whether the project is featured
        created_at (datetime): Timestamp of project creation
        order (int): Display order of the project
    """

    title = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=100)
    services = models.CharField(max_length=200)
    year = models.CharField(max_length=4)
    image = models.ImageField(
        upload_to="projects/",
        blank=True,
        null=True
    )
    category = models.CharField(max_length=100)
    link = models.CharField(max_length=200)
    external_link = models.URLField(blank=True, null=True)
    featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    order = models.IntegerField(default=0)

    class Meta:
        """Meta options for Project model."""
        ordering = ["order", "-created_at"]

    def __str__(self) -> str:
        """Return string representation of the project.

        Returns:
            str: The project title
        """
        return str(self.title)


class ProjectPackage(models.Model):
    """Model representing different project package types and their specifications.

    Attributes:
        name (str): Package type (enterprise, mid-tier, or static)
        base_price (Decimal): Base price for the package
        features (JSON): Features included in the package
        estimated_duration (int): Estimated project duration in days
    """
    PACKAGE_CHOICES = [
        ('enterprise', 'Enterprise Full-Stack Solution'),
        ('mid_tier', 'Mid-Tier Solution'),
        ('static', 'Static Frontend Solution')
    ]
    
    name = models.CharField(max_length=50, choices=PACKAGE_CHOICES)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    features = models.JSONField()
    estimated_duration = models.IntegerField(help_text="Estimated days to completion")
    
    def __str__(self):
        return self.get_name_display()


class ProjectRequirement(models.Model):
    """Model representing specific requirements for a project.

    Attributes:
        project (Project): Foreign key to associated project
        requirement_type (str): Type of requirement
        details (str): Detailed description of requirement
        is_completed (bool): Completion status of requirement
    """
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    requirement_type = models.CharField(max_length=100)
    details = models.TextField()
    is_completed = models.BooleanField(default=False)

    def __str__(self) -> str:
        """Return string representation of the requirement.

        Returns:
            str: The requirement type and project title
        """
        return f"{self.requirement_type} - {self.project.title}"


class Milestone(models.Model):
    """Model representing project milestones.

    Attributes:
        project (Project): Foreign key to associated project
        title (str): Title of the milestone (max 200 characters)
        description (str): Detailed description of the milestone
        due_date (Date): Expected completion date
        is_completed (bool): Whether the milestone is completed
        completion_date (Date): Actual completion date (optional)
    """
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    due_date = models.DateField()
    is_completed = models.BooleanField(default=False)
    completion_date = models.DateField(null=True, blank=True)

    def __str__(self) -> str:
        """Return string representation of the milestone.

        Returns:
            str: The milestone title
        """

class ProjectDeliverable(models.Model):
    """Model representing project deliverable files.

    Attributes:
        project (Project): Foreign key to associated project
        title (str): Title of the deliverable (max 200 characters)
        file (FileField): The actual deliverable file
        version (str): Version identifier (max 50 characters)
        uploaded_at (datetime): Timestamp of upload
    """
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='deliverables/')
    version = models.CharField(max_length=50)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        """Return string representation of the deliverable.

        Returns:
            str: The deliverable title
        """
        return str(self.title)