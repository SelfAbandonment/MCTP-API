"""
Microsoft / Xbox Live / Minecraft Services 4 步换 token 流程

参考: https://wiki.vg/Microsoft_Authentication_Scheme
"""

from __future__ import annotations

import logging
import secrets
from dataclasses import dataclass
from urllib.parse import urlencode

import requests
from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from requests import RequestException

logger = logging.getLogger(__name__)

# OAuth / Auth endpoints
MS_AUTHORIZE_URL = "https://login.live.com/oauth20_authorize.srf"
MS_TOKEN_URL = "https://login.live.com/oauth20_token.srf"
XBL_AUTH_URL = "https://user.auth.xboxlive.com/user/authenticate"
XSTS_AUTH_URL = "https://xsts.auth.xboxlive.com/xsts/authorize"
MC_LOGIN_URL = "https://api.minecraftservices.com/authentication/login_with_xbox"
MC_PROFILE_URL = "https://api.minecraftservices.com/minecraft/profile"
MC_OWNERSHIP_URL = "https://api.minecraftservices.com/entitlements/mcstore"

DEFAULT_SCOPE = "XboxLive.signin offline_access"

REQUEST_TIMEOUT = 15


class MicrosoftOAuthError(Exception):
    """OAuth 流程任意一步失败"""

    def __init__(self, message: str, code: str = "ms_oauth_error", http_status: int = 400):
        super().__init__(message)
        self.code = code
        self.http_status = http_status


@dataclass
class MinecraftProfile:
    uuid: str  # 无破折号 32 字符
    username: str
    ms_refresh_token: str  # 用于后续静默刷新
    ms_account_id: str = ""


def build_authorize_url(state: str) -> str:
    """构造跳转给用户的 Microsoft 授权 URL"""
    params = {
        "client_id": settings.MS_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": settings.MS_REDIRECT_URI,
        "response_mode": "query",
        "scope": DEFAULT_SCOPE,
        "state": state,
        "prompt": "select_account",
    }
    return f"{MS_AUTHORIZE_URL}?{urlencode(params)}"


def gen_state() -> str:
    return secrets.token_urlsafe(32)


# --------------------- 4 步换 token ---------------------


def _ms_exchange_code(code: str) -> dict:
    """Step 1: code -> Microsoft access_token + refresh_token"""
    data = {
        "client_id": settings.MS_CLIENT_ID,
        "client_secret": settings.MS_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": settings.MS_REDIRECT_URI,
        "scope": DEFAULT_SCOPE,
    }
    resp = requests.post(MS_TOKEN_URL, data=data, timeout=REQUEST_TIMEOUT)
    if resp.status_code != 200:
        logger.warning("MS token exchange failed: %s %s", resp.status_code, resp.text[:300])
        raise MicrosoftOAuthError("Microsoft token exchange failed", code="ms_token_failed")
    return resp.json()


def _xbl_authenticate(ms_access_token: str) -> tuple[str, str]:
    """Step 2: MS token -> Xbox Live token + uhs"""
    payload = {
        "Properties": {
            "AuthMethod": "RPS",
            "SiteName": "user.auth.xboxlive.com",
            "RpsTicket": f"d={ms_access_token}",
        },
        "RelyingParty": "http://auth.xboxlive.com",
        "TokenType": "JWT",
    }
    resp = requests.post(
        XBL_AUTH_URL,
        json=payload,
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        timeout=REQUEST_TIMEOUT,
    )
    if resp.status_code != 200:
        logger.warning("XBL auth failed: %s %s", resp.status_code, resp.text[:300])
        raise MicrosoftOAuthError("Xbox Live authentication failed", code="xbl_failed")
    body = resp.json()
    xbl_token = body["Token"]
    uhs = body["DisplayClaims"]["xui"][0]["uhs"]
    return xbl_token, uhs


# Xbox XSTS 已知错误码翻译
_XSTS_ERR_MAP = {
    "2148916233": (
        "该微软账号没有 Xbox 档案，请先到 https://xbox.com 创建一个免费的 Xbox 账户后重试。",
        "xsts_no_xbox_account",
    ),
    "2148916235": (
        "该微软账号所在的国家/地区不支持 Xbox Live。",
        "xsts_country_blocked",
    ),
    "2148916238": (
        "未成年账号需要先通过家长账号添加到家庭组才能使用 Xbox Live。",
        "xsts_minor_account",
    ),
    "2148916236": (
        "该账号需要完成成年人验证。",
        "xsts_adult_verification",
    ),
}


def _xsts_authenticate(xbl_token: str) -> tuple[str, str]:
    """Step 3: XBL -> XSTS token"""
    payload = {
        "Properties": {
            "SandboxId": "RETAIL",
            "UserTokens": [xbl_token],
        },
        "RelyingParty": "rp://api.minecraftservices.com/",
        "TokenType": "JWT",
    }
    resp = requests.post(
        XSTS_AUTH_URL,
        json=payload,
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        timeout=REQUEST_TIMEOUT,
    )
    if resp.status_code == 401:
        body = resp.json() if resp.content else {}
        xerr = str(body.get("XErr", ""))
        msg, code = _XSTS_ERR_MAP.get(xerr, ("Xbox 账号校验失败", "xsts_failed"))
        raise MicrosoftOAuthError(msg, code=code)
    if resp.status_code != 200:
        logger.warning("XSTS failed: %s %s", resp.status_code, resp.text[:300])
        raise MicrosoftOAuthError("XSTS authentication failed", code="xsts_failed")
    body = resp.json()
    xsts_token = body["Token"]
    uhs = body["DisplayClaims"]["xui"][0]["uhs"]
    return xsts_token, uhs


def _mc_login(uhs: str, xsts_token: str) -> str:
    """Step 4: XSTS -> Minecraft access_token"""
    payload = {"identityToken": f"XBL3.0 x={uhs};{xsts_token}"}
    resp = requests.post(
        MC_LOGIN_URL,
        json=payload,
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        timeout=REQUEST_TIMEOUT,
    )
    if resp.status_code == 403 and "Invalid app registration" in resp.text:
        logger.warning("MC app registration invalid: %s", resp.text[:300])
        raise MicrosoftOAuthError(
            "Azure 应用注册配置无效（Microsoft/Minecraft 不接受当前应用配置）",
            code="ms_app_registration_invalid",
        )
    if resp.status_code != 200:
        logger.warning("MC login failed: %s %s", resp.status_code, resp.text[:300])
        raise MicrosoftOAuthError("Minecraft 登录失败", code="mc_login_failed")
    return resp.json()["access_token"]


def _mc_profile(mc_access_token: str) -> tuple[str, str]:
    """获取 Minecraft 玩家档案 (UUID + 用户名)"""
    resp = requests.get(
        MC_PROFILE_URL,
        headers={"Authorization": f"Bearer {mc_access_token}"},
        timeout=REQUEST_TIMEOUT,
    )
    if resp.status_code == 404:
        raise MicrosoftOAuthError(
            "该微软账号未拥有 Minecraft 正版，请先购买后再登录。",
            code="mc_not_owned",
        )
    if resp.status_code != 200:
        logger.warning("MC profile failed: %s %s", resp.status_code, resp.text[:300])
        raise MicrosoftOAuthError("获取 Minecraft 档案失败", code="mc_profile_failed")
    body = resp.json()
    return body["id"], body["name"]


def exchange_code_for_minecraft_profile(code: str) -> MinecraftProfile:
    """完整跑完 4 步流程，返回 Minecraft 档案 + ms_refresh_token"""
    if not settings.MS_CLIENT_ID or not settings.MS_CLIENT_SECRET:
        raise MicrosoftOAuthError(
            "Microsoft OAuth 未配置（MS_CLIENT_ID/SECRET 缺失）",
            code="ms_oauth_not_configured",
            http_status=500,
        )

    try:
        ms = _ms_exchange_code(code)
        ms_access = ms["access_token"]
        ms_refresh = ms.get("refresh_token", "")

        xbl_token, _ = _xbl_authenticate(ms_access)
        xsts_token, uhs = _xsts_authenticate(xbl_token)
        mc_token = _mc_login(uhs, xsts_token)
        uuid, username = _mc_profile(mc_token)
    except RequestException as e:
        logger.warning("Microsoft OAuth upstream network error: %s", e)
        raise MicrosoftOAuthError(
            "无法连接 Microsoft/Xbox 服务，请稍后重试。",
            code="ms_network_error",
            http_status=503,
        ) from e

    return MinecraftProfile(
        uuid=uuid,
        username=username,
        ms_refresh_token=ms_refresh,
        ms_account_id="",
    )


# --------------------- refresh_token 加密存储 ---------------------


def _fernet() -> Fernet | None:
    key = settings.MS_TOKEN_FERNET_KEY
    if not key:
        return None
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt_refresh_token(token: str) -> str:
    if not token:
        return ""
    f = _fernet()
    if f is None:
        # 没配密钥就不存，避免明文落库
        return ""
    return f.encrypt(token.encode()).decode()


def decrypt_refresh_token(enc: str) -> str:
    if not enc:
        return ""
    f = _fernet()
    if f is None:
        return ""
    try:
        return f.decrypt(enc.encode()).decode()
    except InvalidToken:
        logger.warning("Failed to decrypt refresh token (wrong key?)")
        return ""
