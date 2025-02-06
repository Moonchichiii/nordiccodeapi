# projects/models.py
from django.db import models
from django.conf import settings

class ProjectPackage(models.Model):
    """Represents a project package."""
    PACKAGE_TYPES = [
        ('static', 'Static Frontend'),
        ('fullstack', 'Full Stack'),
        ('enterprise', 'Enterprise'),
    ]
    type = models.CharField(max_length=20, choices=PACKAGE_TYPES, unique=True)
    name = models.CharField(max_length=100)
    price_eur_cents = models.PositiveIntegerField(
        help_text='Price in EUR cents (e.g., 60000 for €600.00)'
    )
    price_sek_ore = models.PositiveIntegerField(
        help_text='Price in SEK öre (e.g., 630000 for 6300.00 SEK)'
    )
    description = models.TextField(blank=True)
    features = models.JSONField()
    extra_features = models.JSONField()
    is_active = models.BooleanField(default=True)
    is_recommended = models.BooleanField(default=False)
    support_days = models.PositiveIntegerField(default=30)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['price_eur_cents']

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"

    @property
    def price_eur(self) -> float:
        return self.price_eur_cents / 100

    @property
    def price_sek(self) -> float:
        return self.price_sek_ore / 100


class Addon(models.Model):
    id = models.CharField(primary_key=True, max_length=100)  # Use string as primary key
    name = models.CharField(max_length=100)
    description = models.TextField()
    price_eur_cents = models.PositiveIntegerField(
        help_text='Price in EUR cents (e.g., 10000 for €100.00)'
    )
    price_sek_ore = models.PositiveIntegerField(
        help_text='Price in SEK öre (e.g., 100000 for 1000.00 SEK)'
    )
    compatible_packages = models.ManyToManyField(
        ProjectPackage,
        related_name='compatible_addons'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    @property
    def price_eur(self) -> float:
        return self.price_eur_cents / 100
    
    @property
    def price_sek(self) -> float:
        return self.price_sek_ore / 100



class Project(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('planning', 'Planning Phase'),
        ('pending_approval', 'Pending Client Approval'),
        ('pending_payment', 'Pending Payment'),
        ('development', 'In Development'),
        ('review', 'Review Phase'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='projects'
    )
    package = models.ForeignKey(
        ProjectPackage,
        on_delete=models.PROTECT,
        related_name='projects'
    )
    addons = models.ManyToManyField(
        Addon,
        through='ProjectAddon',
        related_name='projects'
    )
    title = models.CharField(max_length=200, blank=True)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    requirements_doc = models.FileField(
        upload_to='project_requirements/%Y/%m/',
        null=True,
        blank=True
    )
    start_date = models.DateField(null=True, blank=True)
    target_completion_date = models.DateField(null=True, blank=True)
    is_planning_completed = models.BooleanField(default=False)
    is_planning_locked = models.BooleanField(default=True)
    total_price_eur_cents = models.PositiveIntegerField(
        help_text='Total price in EUR cents'
    )
    estimated_hours = models.PositiveIntegerField(null=True, blank=True)
    client_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.user.email}"

    @property
    def total_price_eur(self) -> float:
        return self.total_price_eur_cents / 100

    def calculate_total_price_cents(self) -> int:
        total = self.package.price_eur_cents
        for project_addon in self.projectaddon_set.filter(is_included=False):
            total += project_addon.addon.price_eur_cents
        return total

    def recalc_and_save(self) -> None:
        self.total_price_eur_cents = self.calculate_total_price_cents()
        self.save()

    def approve_planning(self):
        if self.status == 'planning' and not self.is_planning_locked:
            self.client_approved = True
            self.status = 'pending_payment'
            self.save()


class ProjectAddon(models.Model):
    """Through model for project and add-on relationships."""
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    addon = models.ForeignKey(Addon, on_delete=models.PROTECT)
    is_included = models.BooleanField(default=False)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['project', 'addon']

    def __str__(self):
        return f"{self.project.title} - {self.addon.name}"

    def is_included_by_default(self) -> bool:
        return (
            self.project.package.type == 'enterprise'
            and self.addon.compatible_packages.filter(type='enterprise').exists()
        )
