from django.apps import AppConfig
from django.db.models.signals import post_migrate

class ProjectsConfig(AppConfig):
    name = 'projects'

    def ready(self):
        # Import the seeding function and connect the signal.
        from . import signals
        post_migrate.connect(signals.seed_default_packages, sender=self)
