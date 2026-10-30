from __future__ import annotations

from django.apps import AppConfig


class MicrosoftProviderConfig(AppConfig):
    """Custom allauth provider package for Microsoft + Minecraft authentication."""

    name = "mctp_api.auth.microsoft_provider"
    label = "mctp_microsoft"
    verbose_name = "微软登录"
    default_auto_field = "django.db.models.BigAutoField"
