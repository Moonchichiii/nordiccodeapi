from django.db import models
from django.conf import settings
from django.utils import timezone


class Project(models.Model):
    STATUS_CHOICES = [
        ('planning', 'Planning Phase'),
        ('development', 'In Development'),
        ('review', 'Client Review'),
        ('revision', 'In Revision'),
        ('testing', 'Testing'),
        ('deployment', 'Deployment'),
        ('completed', 'Completed'),
        ('maintenance', 'Maintenance'),
    ]

    # Original fields
    title = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=100)
    services = models.CharField(max_length=200)
    year = models.CharField(max_length=4)
    image = models.ImageField(upload_to="projects/", blank=True, null=True)
    category = models.CharField(max_length=100)
    link = models.CharField(max_length=200)
    external_link = models.URLField(blank=True, null=True)
    featured = models.BooleanField(default=False)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='planning'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    order = models.IntegerField(default=0)

    # Financial tracking fields
    # (Point this to the *orders* app’s ProjectOrder, not the “duplicate” one)
    order_link = models.OneToOneField(
        'orders.ProjectOrder',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='related_project'
    )
    total_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    last_payment_date = models.DateTimeField(null=True, blank=True)
    payment_history = models.JSONField(default=list)

    class Meta:
        ordering = ["order", "-created_at"]

    def __str__(self):
        return self.title

    def update_payment_status(self, payment):
        """
        Example method to update payment details whenever a payment is made.
        """
        self.total_paid += payment.amount
        self.last_payment_date = timezone.now()
        self.payment_history.append({
            'amount': str(payment.amount),
            'date': timezone.now().isoformat(),
            'type': payment.payment_type
        })
        self.save()


class ProjectPackage(models.Model):
    PACKAGE_CHOICES = [
        ('enterprise', 'Enterprise Full-Stack Solution'),
        ('mid_tier', 'Mid-Tier Solution'),
        ('static', 'Static Frontend Solution'),
    ]

    name = models.CharField(max_length=50, choices=PACKAGE_CHOICES)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    features = models.JSONField()
    tech_stack = models.JSONField(default=list)
    deliverables = models.JSONField(default=list)
    estimated_duration = models.IntegerField()
    maintenance_period = models.IntegerField(default=30)
    sla_response_time = models.IntegerField(default=24)

    def __str__(self):
        return self.get_name_display()


class ProjectRequirement(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    requirement_type = models.CharField(max_length=100)
    details = models.TextField()
    is_completed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.requirement_type} - {self.project.title}"


class Milestone(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    due_date = models.DateField()
    is_completed = models.BooleanField(default=False)
    completion_date = models.DateField(null=True, blank=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', 'due_date']

    def __str__(self):
        return self.title


class ProjectDeliverable(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='deliverables/')
    version = models.CharField(max_length=50)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class ProjectComment(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    attachments = models.FileField(upload_to='comments/', null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Comment by {self.user} on {self.project.title}"
