import logging
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


class ProjectPackageManager(models.Manager):
    def get_active_packages(self):
        """Get all currently available packages"""
        return self.all()

    def get_package_by_name(self, name):
        """Get package by name safely"""
        try:
            return self.get(name=name)
        except ProjectPackage.DoesNotExist:
            logger.error(f"Package not found: {name}")
            return None


class ProjectPackage(models.Model):
    """
    Model representing different project package offerings with pricing and features.
    """

    class PackageChoices(models.TextChoices):
        ENTERPRISE = "enterprise", _("Enterprise Full-Stack Solution")
        MID_TIER = "mid_tier", _("Mid-Tier Solution")
        STATIC = "static", _("Static Frontend Solution")

    name = models.CharField(
        max_length=50,
        choices=PackageChoices.choices,
        unique=True,
        help_text=_("Type of project package"),
    )
    base_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text=_("Base price for the package"),
    )
    features = models.JSONField(
        help_text=_("Package features in JSON format"), default=dict
    )
    tech_stack = models.JSONField(
        default=list, help_text=_("Technologies used in this package")
    )
    deliverables = models.JSONField(default=list, help_text=_("Project deliverables"))
    estimated_duration = models.PositiveIntegerField(
        help_text=_("Estimated duration in days"), validators=[MinValueValidator(1)]
    )
    maintenance_period = models.PositiveIntegerField(
        default=30,
        help_text=_("Support period in days"),
        validators=[MinValueValidator(1)],
    )
    sla_response_time = models.PositiveIntegerField(
        default=24,
        help_text=_("Response time in hours"),
        validators=[MinValueValidator(1)],
    )

    objects = ProjectPackageManager()

    class Meta:
        verbose_name = _("Project Package")
        verbose_name_plural = _("Project Packages")
        ordering = ["base_price"]

    def __str__(self):
        return self.get_name_display()

    def clean(self):
        """Validate the model"""
        super().clean()
        if self.maintenance_period < 1:
            raise ValidationError(
                {"maintenance_period": _("Maintenance period must be at least 1 day")}
            )
        if self.sla_response_time < 1:
            raise ValidationError(
                {"sla_response_time": _("SLA response time must be at least 1 hour")}
            )

    def get_features_list(self):
        """Return features as a list"""
        return list(self.features.values()) if isinstance(self.features, dict) else []

    @property
    def total_price(self):
        """Calculate total price including all features"""
        return self.base_price


class ProjectQuerySet(models.QuerySet):
    def active(self):
        """Get all non-completed projects"""
        return self.exclude(status=Project.StatusChoices.COMPLETED)

    def by_status(self, status):
        """Filter projects by status"""
        return self.filter(status=status)

    def with_staff(self):
        """Get projects with assigned staff"""
        return self.exclude(assigned_staff__isnull=True)


class ProjectManager(models.Manager):
    def get_queryset(self):
        return ProjectQuerySet(self.model, using=self._db)

    def active(self):
        return self.get_queryset().active()


class Project(models.Model):
    """
    Model representing client projects with their details and status.
    """

    class StatusChoices(models.TextChoices):
        PLANNING = "planning", _("Planning Phase")
        PENDING_PAYMENT = "pending_payment", _("Pending Payment")
        IN_PROGRESS = "in_progress", _("In Progress")
        COMPLETED = "completed", _("Completed")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="projects",
        help_text=_("Project owner"),
    )
    title = models.CharField(max_length=200, help_text=_("Project title"))
    description = models.TextField(help_text=_("Detailed project description"))
    package = models.ForeignKey(
        ProjectPackage,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="projects",
        help_text=_("Selected project package"),
    )
    client_specifications = models.FileField(
        upload_to="client_specs/%Y/%m/",
        validators=[FileExtensionValidator(allowed_extensions=["pdf", "doc", "docx"])],
        null=True,
        blank=True,
        help_text=_("Client-provided documents (PDF, DOC, DOCX)"),
    )
    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.PLANNING,
        help_text=_("Current project status"),
    )
    planning_completed = models.BooleanField(default=False)
    planning_locked = models.BooleanField(default=True)  # Unlocked after payment
    created_at = models.DateTimeField(
        auto_now_add=True, help_text=_("Project creation timestamp")
    )
    assigned_staff = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="assigned_projects",
        blank=True,
        help_text=_("Staff members assigned to this project"),
    )

    objects = ProjectManager()

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("Project")
        verbose_name_plural = _("Projects")
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["user", "created_at"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

    def clean(self):
        """Validate the model"""
        super().clean()
        if self.status == self.StatusChoices.COMPLETED:
            if self.pk and not self.assigned_staff.exists():
                raise ValidationError(
                    {"status": _("Cannot mark as completed without assigned staff")}
                )

    def save(self, *args, **kwargs):
        """Override save to ensure validation"""
        self.full_clean()
        super().save(*args, **kwargs)
        logger.info(f"Project {self.id} saved - Status: {self.status}")

    @property
    def is_active(self):
        """Check if project is active"""
        return self.status != self.StatusChoices.COMPLETED

    @property
    def has_specifications(self):
        """Check if project has client specifications"""
        return bool(self.client_specifications)

    def assign_staff(self, user):
        """Safely assign staff to project"""
        if user.is_staff:
            self.assigned_staff.add(user)
            logger.info(f"Staff member {user.email} assigned to project {self.id}")
        else:
            logger.warning(
                f"Attempted to assign non-staff user {user.email} to project {self.id}"
            )
            raise ValidationError(_("Only staff members can be assigned to projects"))

    def remove_staff(self, user):
        """Safely remove staff from project"""
        self.assigned_staff.remove(user)
        logger.info(f"Staff member {user.email} removed from project {self.id}")
