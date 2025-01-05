from django.db import models

# Create your models here.


class Project(models.Model):
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
    created_at = models.DateTimeField(auto_now_add=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ["order", "-created_at"]

    def __str__(self):
        return self.title
