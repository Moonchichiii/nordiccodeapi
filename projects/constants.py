# projects/constants.py
from django.db import models

class ProjectConstants:
    class PackageTypes(models.TextChoices):
        STATIC = 'static', 'Static Frontend'
        FULLSTACK = 'fullstack', 'Full Stack'
        ENTERPRISE = 'enterprise', 'Enterprise'

    class ProjectStatus(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PENDING_PAYMENT = 'pending_payment', 'Pending Payment'
        PLANNING = 'planning', 'Planning Phase'
        DEVELOPMENT = 'development', 'In Development'
        REVIEW = 'review', 'Review Phase'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'