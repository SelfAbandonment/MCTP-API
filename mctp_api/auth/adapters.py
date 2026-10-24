from __future__ import annotations

from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.models import SocialLogin
from django.http import HttpRequest

from mctp_api.auth.microsoft import encrypt_refresh_token


class MCTPSocialAccountAdapter(DefaultSocialAccountAdapter):
    """Persist Minecraft identity from the custom Microsoft provider.

    allauth owns the account/social-account records; the Minecraft profile is
    kept in the SocialAccount ``extra_data``. Older ``MicrosoftAccount`` rows
    are intentionally not migrated (users re-bind through the new flow).
    """

    def _sync_binding(self, sociallogin: SocialLogin) -> None:
        extra = sociallogin.account.extra_data or {}
        mc_uuid = extra.get("mc_uuid")
        mc_username = extra.get("mc_username")
        if not mc_uuid:
            return
        sociallogin.account.extra_data["mc_uuid"] = mc_uuid
        sociallogin.account.extra_data["mc_username"] = mc_username or ""

        refresh_token = ""
        token = getattr(sociallogin, "token", None)
        if token is not None:
            refresh_token = getattr(token, "token_secret", "") or ""
        if refresh_token:
            encrypted = encrypt_refresh_token(refresh_token)
            if encrypted:
                sociallogin.account.extra_data["ms_refresh_token_enc"] = encrypted

    def pre_social_login(self, request: HttpRequest, sociallogin: SocialLogin) -> None:
        super().pre_social_login(request, sociallogin)
        if sociallogin.is_existing:
            self._sync_binding(sociallogin)
            sociallogin.account.save(update_fields=["extra_data"])

    def save_user(self, request: HttpRequest, sociallogin: SocialLogin, form=None):
        self._sync_binding(sociallogin)
        user = super().save_user(request, sociallogin, form)
        return user
