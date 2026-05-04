"""
Microsoft OAuth 视图

流程:
  GET  /api/v1/auth/microsoft/login/      -> 返回授权 URL（前端 window.location 跳过去）
  GET  /api/v1/auth/microsoft/callback/   -> Microsoft 回调，4 步换 token，
                                              成功后 302 跳转到 FRONTEND_OAUTH_CALLBACK?token=...&refresh=...

设计要点:
  - state 参数走 Django session 防 CSRF
  - 已登录用户走该流程会"绑定"到当前账号；未登录则按 mc_uuid 找/建账号
  - JWT 用 simplejwt 直接签
"""

from __future__ import annotations

import logging
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.http import HttpResponseRedirect
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from mctp_api.auth.microsoft import (
    MicrosoftOAuthError,
    build_authorize_url,
    encrypt_refresh_token,
    exchange_code_for_minecraft_profile,
    gen_state,
)
from mctp_api.auth.models import MicrosoftAccount
from mctp_api.mctp_api_core.response import ApiResponse

logger = logging.getLogger(__name__)
User = get_user_model()

SESSION_STATE_KEY = "ms_oauth_state"
SESSION_BIND_USER_KEY = "ms_oauth_bind_user_id"


def _issue_jwt(user) -> tuple[str, str]:
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token), str(refresh)


def _redirect_frontend(**params) -> HttpResponseRedirect:
    base = settings.FRONTEND_OAUTH_CALLBACK
    sep = "&" if "?" in base else "?"
    return HttpResponseRedirect(f"{base}{sep}{urlencode(params)}")


class MicrosoftLoginView(APIView):
    """发起 Microsoft 登录: 生成 state 并返回授权 URL"""

    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(
        summary="发起 Microsoft 登录",
        description=(
            "返回用户应跳转的 Microsoft 授权 URL。"
            "前端 `window.location.href = data.authorize_url` 即可。"
            "如需把当前已登录账号与微软账号绑定，请在请求 header 携带 JWT，"
            "本接口会把 user_id 暂存到 session，回调时使用。"
        ),
        tags=["认证"],
    )
    def get(self, request):
        if not settings.MS_CLIENT_ID:
            return ApiResponse.error(
                message="Microsoft OAuth 未配置",
                code=503,
                status=503,
            )
        state = gen_state()
        request.session[SESSION_STATE_KEY] = state
        # 已登录用户走绑定模式
        if request.user.is_authenticated:
            request.session[SESSION_BIND_USER_KEY] = request.user.id
        else:
            request.session.pop(SESSION_BIND_USER_KEY, None)
        url = build_authorize_url(state)
        return ApiResponse.success(data={"authorize_url": url, "state": state})


class MicrosoftCallbackView(APIView):
    """Microsoft 回调: 4 步换 token, 找/建用户, 签 JWT, 跳前端"""

    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(
        summary="Microsoft 登录回调",
        description="由 Microsoft 重定向调用，不要手动调。成功后 302 跳前端并携带 JWT。",
        parameters=[
            OpenApiParameter("code", str, OpenApiParameter.QUERY),
            OpenApiParameter("state", str, OpenApiParameter.QUERY),
            OpenApiParameter("error", str, OpenApiParameter.QUERY, required=False),
        ],
        tags=["认证"],
    )
    def get(self, request):
        # 1. 用户拒绝授权 / Microsoft 返回错误
        if err := request.GET.get("error"):
            desc = request.GET.get("error_description", err)
            return _redirect_frontend(error=err, error_description=desc)

        code = request.GET.get("code", "")
        state = request.GET.get("state", "")
        expected_state = request.session.pop(SESSION_STATE_KEY, None)
        bind_user_id = request.session.pop(SESSION_BIND_USER_KEY, None)

        if not code:
            return _redirect_frontend(error="missing_code")
        if not expected_state or state != expected_state:
            return _redirect_frontend(error="invalid_state")

        # 2. 跑 4 步换 token
        try:
            profile = exchange_code_for_minecraft_profile(code)
        except MicrosoftOAuthError as e:
            logger.info("Microsoft OAuth failed: %s (%s)", e, e.code)
            return _redirect_frontend(error=e.code, error_description=str(e))
        except Exception:  # noqa: BLE001
            logger.exception("Microsoft OAuth unexpected error")
            return _redirect_frontend(error="server_error")

        # 3. 找/建/绑定 User + MicrosoftAccount
        user = self._resolve_user(profile, bind_user_id)

        # 4. 签 JWT 跳前端
        access, refresh = _issue_jwt(user)
        return _redirect_frontend(
            access=access,
            refresh=refresh,
            mc_username=profile.username,
            mc_uuid=profile.uuid,
        )

    @transaction.atomic
    def _resolve_user(self, profile, bind_user_id):
        existing = MicrosoftAccount.objects.select_for_update().filter(mc_uuid=profile.uuid).first()

        if bind_user_id:
            # 绑定模式: 当前已登录用户尝试关联此 MC 账号
            try:
                target_user = User.objects.get(pk=bind_user_id)
            except User.DoesNotExist:
                target_user = None

            if existing and target_user and existing.user_id != target_user.id:
                # 该 MC UUID 已被别的账号占用，安全起见拒绝抢占；
                # 这里直接返回原绑定用户，前端可据 mc_username 提示
                logger.warning(
                    "MC UUID %s already bound to user %s, refused to rebind to %s",
                    profile.uuid, existing.user_id, target_user.id,
                )
                return self._touch(existing, profile)

            if existing and target_user and existing.user_id == target_user.id:
                return self._touch(existing, profile)

            if not existing and target_user:
                MicrosoftAccount.objects.create(
                    user=target_user,
                    mc_uuid=profile.uuid,
                    mc_username=profile.username,
                    ms_refresh_token_enc=encrypt_refresh_token(profile.ms_refresh_token),
                    last_login_at=timezone.now(),
                )
                return target_user

        # 非绑定: 已存在直接登录
        if existing:
            return self._touch(existing, profile)

        # 全新用户: 用 mc_username 当 username（冲突则加后缀）
        username = self._unique_username(profile.username)
        user = User.objects.create_user(username=username, email="")
        user.set_unusable_password()
        user.save(update_fields=["password"])

        MicrosoftAccount.objects.create(
            user=user,
            mc_uuid=profile.uuid,
            mc_username=profile.username,
            ms_refresh_token_enc=encrypt_refresh_token(profile.ms_refresh_token),
            last_login_at=timezone.now(),
        )
        return user

    @staticmethod
    def _touch(account: MicrosoftAccount, profile) -> User:
        account.mc_username = profile.username
        if profile.ms_refresh_token:
            account.ms_refresh_token_enc = encrypt_refresh_token(profile.ms_refresh_token)
        account.last_login_at = timezone.now()
        account.save(update_fields=["mc_username", "ms_refresh_token_enc", "last_login_at", "updated_at"])
        return account.user

    @staticmethod
    def _unique_username(base: str) -> str:
        candidate = base
        suffix = 1
        while User.objects.filter(username=candidate).exists():
            suffix += 1
            candidate = f"{base}_{suffix}"
            if suffix > 100:
                # 极端情况兜底
                import secrets
                candidate = f"{base}_{secrets.token_hex(3)}"
                break
        return candidate


class MicrosoftUnbindView(APIView):
    """解绑当前用户的微软/MC 账号"""

    @extend_schema(summary="解绑微软账号", tags=["认证"])
    def delete(self, request):
        deleted, _ = MicrosoftAccount.objects.filter(user=request.user).delete()
        if deleted:
            return ApiResponse.success(message="unbound")
        return ApiResponse.error(message="no microsoft account bound", code=404, status=404)
