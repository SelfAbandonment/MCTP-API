"""
URL configuration for mctp_api project.
"""

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.utils import extend_schema, extend_schema_view
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

token_obtain_view = extend_schema_view(
    post=extend_schema(
        summary="获取 JWT Token",
        description="使用用户名和密码登录，返回短期 access token 与长期 refresh token。",
        tags=["认证"],
    )
)(TokenObtainPairView.as_view())

token_refresh_view = extend_schema_view(
    post=extend_schema(
        summary="刷新 JWT Token",
        description="使用 refresh token 获取新的 access token。启用轮换时会同时返回新的 refresh token。",
        tags=["认证"],
    )
)(TokenRefreshView.as_view())

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),
    # API v1
    path("api/v1/", include("mctp_api.mctp_api_core.urls")),
    # 用户认证
    path("api/v1/auth/", include("mctp_api.auth.urls")),
    # JWT Token
    path("api/v1/auth/token/", token_obtain_view, name="token_obtain_pair"),
    path("api/v1/auth/token/refresh/", token_refresh_view, name="token_refresh"),
    # API 文档
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]
