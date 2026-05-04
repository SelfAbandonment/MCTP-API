from django.apps import AppConfig


class AuthConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "mctp_api.auth"
    label = "mctp_auth"
    verbose_name = "Authentication"
