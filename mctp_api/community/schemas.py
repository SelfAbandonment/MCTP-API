from drf_spectacular.utils import extend_schema_serializer, inline_serializer
from rest_framework import serializers

from .serializers import (
    AnnouncementSerializer,
    CommunityOverviewSerializer,
    PlayerSerializer,
    PublicAnnouncementSerializer,
)


def envelope(name, data):
    serializer = inline_serializer(
        name,
        fields={
            "code": serializers.IntegerField(),
            "message": serializers.CharField(),
            "data": data,
        },
    )
    extend_schema_serializer(many=False)(serializer.__class__)
    return serializer


def paginated(name, item):
    page = inline_serializer(
        f"{name}Page",
        fields={
            "results": item(many=True),
            "count": serializers.IntegerField(),
            "next": serializers.URLField(allow_null=True),
            "previous": serializers.URLField(allow_null=True),
        },
    )
    return envelope(f"{name}ListResponse", page)


PUBLIC_LIST = paginated("PublicAnnouncement", PublicAnnouncementSerializer)
PUBLIC_DETAIL = envelope("PublicAnnouncementResponse", PublicAnnouncementSerializer())
ANNOUNCEMENT_LIST = paginated("Announcement", AnnouncementSerializer)
ANNOUNCEMENT_DETAIL = envelope("AnnouncementResponse", AnnouncementSerializer())
PLAYER_LIST = paginated("Player", PlayerSerializer)
PLAYER_DETAIL = envelope("PlayerResponse", PlayerSerializer())
OVERVIEW_RESPONSE = envelope("CommunityOverviewResponse", CommunityOverviewSerializer())
DELETE_RESPONSE = envelope("AnnouncementDeleteResponse", serializers.JSONField(allow_null=True))
ERROR_RESPONSE = envelope("CommunityErrorResponse", serializers.JSONField(allow_null=True))
