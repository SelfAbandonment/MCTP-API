from django.conf import settings
from django.db import models
from django.db.models import Q


class PointAccount(models.Model):
    """每个玩家一个积分账户；只能由 staff 发放，不提供消费/签到。"""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="point_account",
    )
    balance = models.PositiveIntegerField(default=0)
    total_granted = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "积分账户"
        verbose_name_plural = "积分账户"
        ordering = ["-balance", "-id"]
        indexes = [models.Index(fields=["-balance"])]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.user_id}:{self.balance}"


class PointGrant(models.Model):
    """一次积分发放记录，同时保存发放后的余额用于审计。"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="point_grants",
    )
    amount = models.PositiveIntegerField()
    reason = models.CharField(max_length=120)
    note = models.CharField(max_length=240, blank=True, default="")
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="point_grants_issued",
    )
    balance_after = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "积分发放"
        verbose_name_plural = "积分发放"
        ordering = ["-created_at", "-id"]
        indexes = [models.Index(fields=["user", "-created_at"])]
        constraints = [
            models.CheckConstraint(condition=Q(amount__gt=0), name="points_grant_amount_positive"),
        ]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.user_id}:+{self.amount}"
