from django.db import models
from django.contrib.postgres.indexes import GinIndex
from django.core.cache import cache
from asgiref.sync import sync_to_async

class PlannerSubmission(models.Model):
    project = models.OneToOneField(
        'projects.Project',
        on_delete=models.CASCADE,
        related_name="planner_submission",
        db_index=True
    )
    submission_data = models.JSONField(db_index=True)
    client_summary = models.TextField(blank=True, null=True)
    website_template = models.TextField(blank=True, null=True)
    developer_worksheet = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        indexes = [
            GinIndex(fields=['submission_data']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"Submission {self.pk} at {self.created_at}"

    def save(self, *args, **kwargs):
        cache_key = f'planner_submission_{self.project_id}'
        cache.delete(cache_key)
        super().save(*args, **kwargs)

    @classmethod
    async def acreate(cls, **kwargs):
        return await sync_to_async(cls.objects.create)(**kwargs)
