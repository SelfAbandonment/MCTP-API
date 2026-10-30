from __future__ import annotations

from allauth.socialaccount.providers.oauth2.provider import OAuth2Provider

from .views import MinecraftMicrosoftOAuth2Adapter


class MinecraftMicrosoftProvider(OAuth2Provider):
    """Microsoft identity provider that also verifies the Minecraft profile.

    allauth's built-in Microsoft provider only talks to Microsoft Graph
    (``User.Read``). Minecraft authentication needs the Xbox Live consumer
    endpoint with the ``XboxLive.signin`` scope, followed by the
    Xbox/XSTS/Minecraft Services exchange. This provider keeps allauth's
    account/social wiring while reusing the existing Minecraft pipeline.
    """

    id = "microsoft"
    name = "Microsoft"
    oauth2_adapter_class = MinecraftMicrosoftOAuth2Adapter

    def get_default_scope(self) -> list[str]:
        return ["XboxLive.signin", "offline_access"]

    def extract_uid(self, data) -> str:
        # The Minecraft UUID is the stable identity for this community.
        return str(data["mc_uuid"])

    def extract_common_fields(self, data) -> dict:
        return {"username": data.get("mc_username") or "player"}


provider_classes = [MinecraftMicrosoftProvider]
