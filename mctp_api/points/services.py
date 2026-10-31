from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import F

from .models import PointAccount, PointGrant


def account_for(user) -> PointAccount:
    """读取（必要时创建）账户，保证首次访问就能看到 0 分。"""
    PointAccount.objects.get_or_create(user=user)
    return PointAccount.objects.get(user=user)


def rank_for(account: PointAccount) -> int:
    """余额排名，余额相同按账户 id 稳定排序。"""
    return (
        PointAccount.objects.filter(balance__gt=account.balance).count()
        + PointAccount.objects.filter(balance=account.balance, id__lt=account.id).count()
        + 1
    )


@transaction.atomic
def grant_points(*, user, amount: int, reason: str, note: str = "", granted_by=None) -> tuple[PointAccount, PointGrant]:
    """staff 发放积分：锁账户、加余额、记流水，一次事务完成。"""
    if amount <= 0:
        raise ValueError("amount must be positive")
    PointAccount.objects.get_or_create(user=user)
    account = PointAccount.objects.select_for_update().get(user=user)
    account.balance = F("balance") + amount
    account.total_granted = F("total_granted") + amount
    account.save(update_fields=["balance", "total_granted", "updated_at"])
    account.refresh_from_db(fields=["balance", "total_granted"])
    grant = PointGrant.objects.create(
        user=user,
        amount=amount,
        reason=reason,
        note=note,
        granted_by=granted_by,
        balance_after=account.balance,
    )
    return account, grant


def user_queryset():
    return get_user_model().objects.select_related("point_account").order_by("id")
