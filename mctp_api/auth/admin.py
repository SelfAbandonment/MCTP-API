from django.contrib import admin

from mctp_api.auth.models import MicrosoftAccount


@admin.register(MicrosoftAccount)
class MicrosoftAccountAdmin(admin.ModelAdmin):
    list_display = ("user", "mc_username", "mc_uuid", "last_login_at", "created_at")
    search_fields = ("user__username", "mc_username", "mc_uuid")
    readonly_fields = ("created_at", "updated_at", "last_login_at", "ms_refresh_token_enc")
