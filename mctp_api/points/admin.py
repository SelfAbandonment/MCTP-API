from django.contrib import admin

from .models import PointAccount, PointGrant


@admin.register(PointAccount)
class PointAccountAdmin(admin.ModelAdmin):
    list_display = ("user", "balance", "total_granted", "updated_at")
    search_fields = ("user__username", "user__email")
    readonly_fields = ("balance", "total_granted", "created_at", "updated_at")

    def has_add_permission(self, request):
        return False


@admin.register(PointGrant)
class PointGrantAdmin(admin.ModelAdmin):
    list_display = ("user", "amount", "reason", "granted_by", "balance_after", "created_at")
    list_filter = ("created_at",)
    search_fields = ("user__username", "reason", "granted_by__username")
    readonly_fields = (
        "user",
        "amount",
        "reason",
        "note",
        "granted_by",
        "balance_after",
        "created_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
