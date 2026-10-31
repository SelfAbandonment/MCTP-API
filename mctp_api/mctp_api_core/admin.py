from __future__ import annotations

import json

from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount, SocialApp, SocialToken
from django.apps import apps as django_apps
from django.contrib import admin
from django.contrib.admin.sites import NotRegistered
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.contrib.sites.models import Site
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from unfold.admin import ModelAdmin

from mctp_api.auth.models import MicrosoftAccount
from mctp_api.community.models import Announcement

User = get_user_model()

# Third-party app labels are English by default (allauth/token_blacklist). Set
# them once here so the Unfold sidebar/index is consistently Chinese.
for _label, _name in (
    ("auth", "玩家与账户"),
    ("account", "账户"),
    ("socialaccount", "社交账户"),
    ("token_blacklist", "登录令牌"),
    ("sites", "站点"),
):
    try:
        django_apps.get_app_config(_label).verbose_name = _name
    except LookupError:
        pass

# Chinese model labels for admin pages (display only, no migration).
for _model, _name, _plural in (
    (Announcement, "公告", "公告"),
    (Group, "用户组", "用户组"),
    (User, "玩家", "玩家"),
    (Site, "站点", "站点"),
):
    _model._meta.verbose_name = _name
    _model._meta.verbose_name_plural = _plural

# Third-party models keep English verbose names; translate the labels that are
# actually rendered in the admin (no database migration required).
_LABELS = {
    SocialAccount: ("微软绑定", "微软绑定"),
    SocialApp: ("社交应用", "社交应用"),
    SocialToken: ("社交令牌", "社交令牌"),
    EmailAddress: ("邮箱", "邮箱"),
    MicrosoftAccount: ("旧版 MC 绑定", "旧版 MC 绑定"),
    OutstandingToken: ("有效令牌", "有效令牌"),
    BlacklistedToken: ("已拉黑令牌", "已拉黑令牌"),
}
for _model, (_singular, _plural) in _LABELS.items():
    _model._meta.verbose_name = _singular
    _model._meta.verbose_name_plural = _plural


def _unregister(model) -> None:
    try:
        admin.site.unregister(model)
    except NotRegistered:
        pass


for _hidden in (SocialApp, SocialToken, OutstandingToken, BlacklistedToken):
    _unregister(_hidden)

for _model in (User, Group, Site, SocialAccount, EmailAddress, MicrosoftAccount):
    _unregister(_model)


@admin.register(User)
class PlayerAdmin(BaseUserAdmin, ModelAdmin):
    list_display = ("username", "email", "mc_binding", "is_active", "is_staff", "last_login", "date_joined")
    list_filter = ("is_active", "is_staff", "is_superuser")
    search_fields = ("username", "email", "microsoft_account__mc_username", "socialaccount__uid")
    ordering = ("username",)
    list_per_page = 50
    readonly_fields = ("last_login", "date_joined")
    fieldsets = (
        ("账户", {"fields": ("username", "password", "email")}),
        ("权限", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("时间", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            "创建玩家",
            {
                "classes": ("wide",),
                "fields": ("username", "email", "password1", "password2", "is_staff", "is_active"),
            },
        ),
    )

    @admin.display(description="MC 账号")
    def mc_binding(self, obj):
        social = SocialAccount.objects.filter(user=obj, provider="microsoft").first()
        if social:
            extra = social.extra_data or {}
            return extra.get("mc_username") or social.uid
        legacy = getattr(obj, "microsoft_account", None)
        return legacy.mc_username if legacy else "—"


@admin.register(Group)
class UserGroupAdmin(ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(Site)
class CommunitySiteAdmin(ModelAdmin):
    list_display = ("domain", "name")
    search_fields = ("domain", "name")


@admin.register(SocialAccount)
class SocialBindingAdmin(ModelAdmin):
    list_display = ("user", "provider", "mc_username", "mc_uuid", "date_joined", "last_login")
    list_filter = ("provider",)
    search_fields = ("user__username", "uid")
    ordering = ("-date_joined",)
    readonly_fields = ("user", "provider", "uid", "last_login", "date_joined", "binding_summary")
    fieldsets = (
        ("绑定账户", {"fields": ("user", "provider", "uid")}),
        ("Minecraft", {"fields": ("binding_summary",)}),
        ("时间", {"fields": ("date_joined", "last_login")}),
    )

    @admin.display(description="MC 用户名")
    def mc_username(self, obj):
        return (obj.extra_data or {}).get("mc_username") or "—"

    @admin.display(description="MC UUID")
    def mc_uuid(self, obj):
        return (obj.extra_data or {}).get("mc_uuid") or obj.uid

    @admin.display(description="绑定信息")
    def binding_summary(self, obj):
        extra = dict(obj.extra_data or {})
        extra.pop("ms_refresh_token_enc", None)
        return json.dumps(extra, ensure_ascii=False, indent=2)


@admin.register(EmailAddress)
class EmailAddressAdmin(ModelAdmin):
    list_display = ("user", "email", "verified", "primary")
    list_filter = ("verified", "primary")
    search_fields = ("user__username", "email")
    ordering = ("user__username",)


@admin.register(MicrosoftAccount)
class LegacyMicrosoftBindingAdmin(ModelAdmin):
    list_display = ("user", "mc_username", "mc_uuid", "created_at", "last_login_at")
    search_fields = ("user__username", "mc_username", "mc_uuid")
    ordering = ("-created_at",)
    readonly_fields = (
        "user",
        "mc_uuid",
        "mc_username",
        "mc_name",
        "mc_id",
        "ms_account_id",
        "created_at",
        "updated_at",
        "last_login_at",
    )
    fieldsets = (
        ("旧版绑定（只读，已停止写入）", {"fields": ("user", "mc_name", "mc_id")}),
        ("时间", {"fields": ("created_at", "updated_at", "last_login_at")}),
    )

    @admin.display(description="MC 用户名")
    def mc_name(self, obj):
        return obj.mc_username

    @admin.display(description="MC ID")
    def mc_id(self, obj):
        return obj.mc_uuid

    def has_add_permission(self, request):
        return False


# ---------------------------- admin index curation ----------------------------

_original_get_app_list = admin.site.get_app_list


def _curated_get_app_list(request, app_label=None):
    """Hide noisy third-party app buckets from the index.

    The sidebar still exposes every curated model; the index only keeps the
    three groups operators actually use, all in Chinese.
    """
    if app_label:
        return _original_get_app_list(request, app_label)
    raw = _original_get_app_list(request)
    by_label = {app["app_label"]: app for app in raw}

    def group(name, labels):
        models = []
        app_url = ""
        for label in labels:
            app = by_label.get(label)
            if not app:
                continue
            models.extend(app["models"])
            app_url = app_url or app.get("app_url", "")
        return {
            "name": name,
            "app_label": name,
            "app_url": app_url,
            "has_module_perms": bool(models),
            "models": models,
        }

    return [
        group("社区运营", ["community"]),
        group("玩家与账户", ["auth", "account", "socialaccount", "mctp_auth"]),
        group("系统", ["sites"]),
    ]


admin.site.get_app_list = _curated_get_app_list
admin.site.site_header = "MCTP · 方块社区"
admin.site.site_title = "MCTP 管理后台"
admin.site.index_title = "运营概览"
