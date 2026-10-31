from django.contrib import admin
from django.utils import timezone
from unfold.admin import ModelAdmin

from .models import Announcement


@admin.register(Announcement)
class AnnouncementAdmin(ModelAdmin):
    list_display = ("title", "category", "is_pinned", "is_published", "published_at", "updated_at")
    list_editable = ("category", "is_pinned", "is_published")
    list_filter = ("category", "is_pinned", "is_published")
    list_filter_sheet = True
    search_fields = ("title", "summary")
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "published_at"
    ordering = ("-is_pinned", "-published_at")
    list_per_page = 50

    fieldsets = (
        ("基本信息", {"fields": ("title", "summary", "category")}),
        ("内容", {"fields": ("body",)}),
        ("发布", {"fields": ("is_published", "is_pinned", "published_at")}),
        ("时间戳", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    compressed_fields = True
    warn_unsaved_form = True

    def save_model(self, request, obj, form, change):
        assert isinstance(obj, Announcement)
        if change:
            old = Announcement.objects.filter(pk=obj.pk).only("is_published").first()
            if old and not old.is_published and obj.is_published:
                obj.published_at = timezone.now()
        elif obj.is_published:
            obj.published_at = timezone.now()
        super().save_model(request, obj, form, change)
