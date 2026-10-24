from __future__ import annotations

from allauth.socialaccount.models import SocialAccount
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from mctp_api.auth.models import MicrosoftAccount
from mctp_api.auth.serializers import UserSerializer
from mctp_api.mctp_api_core.response import ApiResponse


class EmptySerializer(serializers.Serializer):
    """Schema marker for views without a request body."""


class SafeTokenRefreshView(TokenRefreshView):
    """Return 401 instead of 500 when a refresh token references a deleted user."""

    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except (get_user_model().DoesNotExist, ObjectDoesNotExist):
            return ApiResponse.unauthorized("登录已失效，请重新登录")


class SessionTokenObtainView(APIView):
    """Exchange an allauth browser session for the SimpleJWT pair used by the API.

    The SPA logs in / signs up / completes Microsoft OAuth through the allauth
    headless browser endpoints (session cookie + CSRF). It then calls this
    endpoint to obtain the Bearer tokens used by all ``/api/v1/`` endpoints.
    """

    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = EmptySerializer

    @extend_schema(
        summary="用 allauth 会话换取 JWT",
        description="需要已登录的 Django session cookie；返回与 /api/v1/auth/token/ 相同的 access/refresh。",
        request=None,
        responses={200: EmptySerializer},
        tags=["认证"],
    )
    def post(self, request):
        refresh = RefreshToken.for_user(request.user)
        return ApiResponse.success(
            data={
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": UserSerializer(request.user).data,
            },
            message="session exchanged",
        )


class MicrosoftUnbindView(APIView):
    """Disconnect the Microsoft/Minecraft social account from the current user."""

    permission_classes = [IsAuthenticated]
    serializer_class = EmptySerializer

    @extend_schema(summary="解绑微软/Minecraft 账号", request=None, responses={200: EmptySerializer}, tags=["认证"])
    def delete(self, request):
        social_deleted, _ = SocialAccount.objects.filter(
            user=request.user,
            provider="microsoft",
        ).delete()
        legacy_deleted, _ = MicrosoftAccount.objects.filter(user=request.user).delete()
        if social_deleted or legacy_deleted:
            return ApiResponse.success(message="unbound")
        return ApiResponse.error(message="no microsoft account bound", code=404, status=404)
