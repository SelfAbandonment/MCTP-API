from django.db import models


class Announcement(models.Model):
    title = models.CharField(max_length=160)
    summary = models.CharField(max_length=240, blank=True, default="")
    body = models.TextField()
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-published_at", "-id"]
        indexes = [models.Index(fields=["is_published", "published_at"])]

    def __str__(self):
        return self.title
