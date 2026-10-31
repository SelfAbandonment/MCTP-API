from django.contrib.auth import get_user_model
from django.utils import timezone
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .models import Announcement


class StrictInputMixin:
    """Reject unrecognized and read-only inputs rather than silently discarding them."""

    def to_internal_value(self, data):
        if isinstance(data, dict):
            writable = {name for name, field in self.fields.items() if not field.read_only}
            unexpected = set(data) - writable
            if unexpected:
                raise serializers.ValidationError({name: ["This field is not writable."] for name in unexpected})
        return super().to_internal_value(data)


class PublicAnnouncementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Announcement
        fields = ("id", "title", "summary", "body", "category", "is_pinned", "published_at", "updated_at")
        read_only_fields = fields


class AnnouncementSerializer(StrictInputMixin, serializers.ModelSerializer):
    class Meta:
        model = Announcement
        fields = (
            "id",
            "title",
            "summary",
            "body",
            "category",
            "is_pinned",
            "is_published",
            "published_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def validate(self, attrs):
        published = attrs.get("is_published", getattr(self.instance, "is_published", False))
        published_at = attrs.get("published_at", getattr(self.instance, "published_at", None))
        if published and published_at is None:
            attrs["published_at"] = timezone.now()
        return attrs


class MinecraftPlayerSerializer(serializers.Serializer):
    uuid = serializers.CharField(read_only=True)
    username = serializers.CharField(read_only=True)


class PlayerSerializer(serializers.ModelSerializer):
    minecraft = serializers.SerializerMethodField()

    class Meta:
        model = get_user_model()
        fields = (
            "id",
            "username",
            "email",
            "is_active",
            "is_staff",
            "is_superuser",
            "date_joined",
            "last_login",
            "minecraft",
        )
        read_only_fields = fields

    @extend_schema_field(MinecraftPlayerSerializer(allow_null=True))
    def get_minecraft(self, obj):
        """优先读取 allauth 绑定，其次回退到旧表。

        新流程的绑定关系存在 ``SocialAccount.extra_data``（见
        ``mctp_api.auth.adapters``），``MicrosoftAccount`` 只保留历史数据。
        使用 ``socialaccount_set.all()`` 让列表视图的 prefetch 只发一次查询。
        """
        for social in obj.socialaccount_set.all():
            if social.provider != "microsoft":
                continue
            extra = social.extra_data or {}
            if extra.get("mc_uuid"):
                return {
                    "uuid": extra["mc_uuid"],
                    "username": extra.get("mc_username", ""),
                }

        legacy = getattr(obj, "microsoft_account", None)
        if legacy is None:
            return None
        return {"uuid": legacy.mc_uuid, "username": legacy.mc_username}


class PlayerUpdateSerializer(StrictInputMixin, serializers.Serializer):
    is_active = serializers.BooleanField(required=True)

    def validate(self, attrs):
        if "is_active" not in attrs:
            raise serializers.ValidationError({"is_active": ["This field is required."]})
        return attrs


class AnnouncementOverviewSerializer(serializers.Serializer):
    published = serializers.IntegerField()
    latest_published_at = serializers.DateTimeField(allow_null=True)


class PlayerOverviewSerializer(serializers.Serializer):
    total = serializers.IntegerField()
    active = serializers.IntegerField()
    minecraft_bound = serializers.IntegerField()


class CommunityOverviewSerializer(serializers.Serializer):
    """玩家中心「社区近况」面板的只读计数器。"""

    announcements = AnnouncementOverviewSerializer()
    players = PlayerOverviewSerializer()
    generated_at = serializers.DateTimeField()
