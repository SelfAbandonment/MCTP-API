from django.db import models


class Announcement(models.Model):
    class Category(models.TextChoices):
        NOTICE = "notice", "公告"
        EVENT = "event", "活动"
        UPDATE = "update", "更新"
        MAINTENANCE = "maintenance", "维护"

    title = models.CharField(max_length=160)
    summary = models.CharField(max_length=240, blank=True, default="")
    body = models.TextField()
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.NOTICE)
    is_pinned = models.BooleanField(default=False)
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_pinned", "-published_at", "-id"]
        indexes = [
            models.Index(fields=["is_published", "published_at"]),
            models.Index(fields=["category", "is_pinned"]),
        ]

    def __str__(self):
        return self.title
