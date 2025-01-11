from django.conf import settings
from django.db import models


class Project(models.Model):
    STATUS_CHOICES = [
        ("planning", "Planning Phase"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="projects",
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    package = models.ForeignKey(
        "ProjectPackage", on_delete=models.SET_NULL, null=True, blank=True
    )
    client_specifications = models.FileField(
        upload_to="client_specs/", blank=True, null=True,
        help_text="Client-provided documents for project customization.",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="planning")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class ProjectPackage(models.Model):
    PACKAGE_CHOICES = [
        ("enterprise", "Enterprise Full-Stack Solution"),
        ("mid_tier", "Mid-Tier Solution"),
        ("static", "Static Frontend Solution"),
    ]

    name = models.CharField(max_length=50, choices=PACKAGE_CHOICES, unique=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    features = models.JSONField()
    tech_stack = models.JSONField(default=list)
    deliverables = models.JSONField(default=list)
    estimated_duration = models.IntegerField(help_text="Duration in days")
    maintenance_period = models.IntegerField(default=30, help_text="Days of support")
    sla_response_time = models.IntegerField(default=24, help_text="Response time in hours")

    def __str__(self):
        return self.get_name_display()



assigned_staff = models.ManyToManyField(
    settings.AUTH_USER_MODEL,
    related_name='assigned_projects',
    blank=True
)