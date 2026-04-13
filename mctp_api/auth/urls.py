"""
认证模块 URL 配置
"""

from django.urls import path

from mctp_api.auth.views import ChangePasswordView, MeView, RegisterView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="auth-register"),
    path("me/", MeView.as_view(), name="auth-me"),
    path("password/", ChangePasswordView.as_view(), name="auth-change-password"),
]
