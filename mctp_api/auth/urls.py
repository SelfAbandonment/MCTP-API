"""
认证模块 URL 配置

Microsoft/Minecraft 登录由 django-allauth 接管（/accounts/ + /_allauth/）；
这里保留 API 侧的 JWT 入口，以及“allauth 会话 -> JWT”的桥接端点。
"""

from django.urls import path

from mctp_api.auth.session_views import MicrosoftUnbindView, SessionTokenObtainView
from mctp_api.auth.views import ChangePasswordView, MeView, RegisterView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="auth-register"),
    path("me/", MeView.as_view(), name="auth-me"),
    path("password/", ChangePasswordView.as_view(), name="auth-change-password"),
    # allauth browser session -> SimpleJWT pair (used by the SPA after login)
    path("token/session/", SessionTokenObtainView.as_view(), name="auth-session-token"),
    # Microsoft / Minecraft social account disconnect
    path("microsoft/unbind/", MicrosoftUnbindView.as_view(), name="auth-ms-unbind"),
]
