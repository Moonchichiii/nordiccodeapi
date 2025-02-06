from django.db import models

PACKAGE_TYPES = [
    ('static', 'Static Frontend'),
    ('fullstack', 'Full Stack'),
    ('enterprise', 'Enterprise'),
]


class ProjectStatus(models.TextChoices):
    DRAFT = 'draft', 'Draft'
    PENDING_PAYMENT = 'pending_payment', 'Pending Payment'
    PLANNING = 'planning', 'Planning Phase'
    DEVELOPMENT = 'development', 'In Development'
    REVIEW = 'review', 'Review Phase'
    COMPLETED = 'completed', 'Completed'
    CANCELLED = 'cancelled', 'Cancelled'