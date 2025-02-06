from django.db import models

class PlannerSubmission(models.Model):
    submission_data = models.JSONField()
    client_summary = models.TextField(blank=True, null=True)
    developer_worksheet = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"Submission {self.pk} at {self.created_at}"
