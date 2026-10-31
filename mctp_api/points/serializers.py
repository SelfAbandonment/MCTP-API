from rest_framework import serializers

from .models import PointGrant


class StrictInputMixin:
    """拒绝未声明字段，避免发放接口被塞入意外字段。"""

    def to_internal_value(self, data):
        if isinstance(data, dict):
            writable = {name for name, field in self.fields.items() if not field.read_only}
            unexpected = set(data) - writable
            if unexpected:
                raise serializers.ValidationError({name: ["This field is not writable."] for name in unexpected})
        return super().to_internal_value(data)


class PointGrantSerializer(serializers.ModelSerializer):
    granted_by = serializers.CharField(source="granted_by.username", read_only=True, allow_null=True)

    class Meta:
        model = PointGrant
        fields = ("id", "amount", "reason", "note", "granted_by", "balance_after", "created_at")
        read_only_fields = fields


class AccountSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    username = serializers.CharField()
    balance = serializers.IntegerField()
    total_granted = serializers.IntegerField()


class MyPointsSerializer(serializers.Serializer):
    account = AccountSerializer()
    rank = serializers.IntegerField()
    recent_grants = PointGrantSerializer(many=True)


class LeaderboardEntrySerializer(serializers.Serializer):
    rank = serializers.IntegerField()
    user_id = serializers.IntegerField()
    username = serializers.CharField()
    balance = serializers.IntegerField()


class ManagePointAccountSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(source="id")
    username = serializers.CharField()
    email = serializers.EmailField(allow_blank=True)
    balance = serializers.SerializerMethodField()
    total_granted = serializers.SerializerMethodField()

    def get_balance(self, obj) -> int:
        account = getattr(obj, "point_account", None)
        return account.balance if account else 0

    def get_total_granted(self, obj) -> int:
        account = getattr(obj, "point_account", None)
        return account.total_granted if account else 0


class GrantCreateSerializer(StrictInputMixin, serializers.Serializer):
    user_id = serializers.IntegerField(min_value=1)
    amount = serializers.IntegerField(min_value=1, max_value=1_000_000)
    reason = serializers.CharField(max_length=120, allow_blank=False)
    note = serializers.CharField(max_length=240, required=False, allow_blank=True, default="")


class GrantResultSerializer(serializers.Serializer):
    account = AccountSerializer()
    grant = PointGrantSerializer()
