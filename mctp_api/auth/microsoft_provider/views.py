from __future__ import annotations

import logging

from allauth.socialaccount.providers.oauth2.views import (
    OAuth2Adapter,
    OAuth2CallbackView,
    OAuth2LoginView,
)
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest

from mctp_api.auth.microsoft import (
    MS_AUTHORIZE_URL,
    MS_TOKEN_URL,
    MicrosoftOAuthError,
    complete_minecraft_login,
    encrypt_refresh_token,
)

logger = logging.getLogger(__name__)


class MinecraftMicrosoftOAuth2Adapter(OAuth2Adapter):
    """allauth OAuth2 adapter using the consumer (Xbox Live) Microsoft endpoint."""

    provider_id = "microsoft"
    authorize_url = MS_AUTHORIZE_URL
    access_token_url = MS_TOKEN_URL

    def complete_login(self, request: HttpRequest, app, token, **kwargs):
        try:
            profile = complete_minecraft_login(
                token.token,
                getattr(token, "token_secret", "") or "",
            )
        except MicrosoftOAuthError as exc:
            logger.info("Minecraft Microsoft login rejected: %s (%s)", exc, exc.code)
            # The allauth callback catches PermissionDenied and redirects back
            # to the frontend with a login error.
            raise PermissionDenied(str(exc)) from exc

        data = {
            "id": profile.uuid,
            "mc_uuid": profile.uuid,
            "mc_username": profile.username,
            "ms_account_id": profile.ms_account_id,
        }
        login = self.get_provider().sociallogin_from_response(request, data)
        # Keep the refresh token encrypted at rest. allauth does not store
        # social tokens by default (SOCIALACCOUNT_STORE_TOKENS=False).
        login.account.extra_data["ms_refresh_token_enc"] = encrypt_refresh_token(profile.ms_refresh_token)
        login.account.extra_data["mc_uuid"] = profile.uuid
        login.account.extra_data["mc_username"] = profile.username
        return login


oauth2_login = OAuth2LoginView.adapter_view(MinecraftMicrosoftOAuth2Adapter)
oauth2_callback = OAuth2CallbackView.adapter_view(MinecraftMicrosoftOAuth2Adapter)
