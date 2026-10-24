from __future__ import annotations

from allauth.socialaccount.providers.oauth2.urls import default_urlpatterns

from .provider import MinecraftMicrosoftProvider

urlpatterns = default_urlpatterns(MinecraftMicrosoftProvider)
