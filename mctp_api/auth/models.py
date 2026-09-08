"""
Microsoft / Minecraft 账号关联模型

通过 OneToOne 关联到 Django 内置 User，保留默认 User 模型不动，
副作用最小，方便后续扩展（白名单、绑定状态等）。
"""

from __future__ import annotations

from django.conf import settings
from django.db import models


class MicrosoftAccount(models.Model):
    """与微软/Minecraft 账号绑定关系"""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="microsoft_account",
    )
    # Minecraft 玩家 UUID（无破折号格式，32 字符）
    mc_uuid = models.CharField(max_length=32, unique=True, db_index=True)
    # 当前 MC 用户名（可能改名，每次登录刷新）
    mc_username = models.CharField(max_length=32)
    # Microsoft 账号 ID（可选，方便去重 / 审计）
    ms_account_id = models.CharField(max_length=128, blank=True, default="")
    # 加密后的 refresh_token（Fernet 加密），用于后续静默刷新拿最新用户名/皮肤
    ms_refresh_token_enc = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Microsoft Account"
        verbose_name_plural = "Microsoft Accounts"

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.user_id}:{self.mc_username}({self.mc_uuid})"
