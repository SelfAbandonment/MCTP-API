from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import generics
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.filters import SearchFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, BasePermission, IsAuthenticated
from rest_framework.views import APIView

from mctp_api.mctp_api_core.response import ApiResponse

from .models import Announcement
from .schemas import (
    ANNOUNCEMENT_DETAIL,
    ANNOUNCEMENT_LIST,
    DELETE_RESPONSE,
    ERROR_RESPONSE,
    OVERVIEW_RESPONSE,
    PLAYER_DETAIL,
    PLAYER_LIST,
    PUBLIC_DETAIL,
    PUBLIC_LIST,
)
from .serializers import (
    AnnouncementSerializer,
    CommunityOverviewSerializer,
    PlayerSerializer,
    PlayerUpdateSerializer,
    PublicAnnouncementSerializer,
)

PUBLIC_ORDERING = ("-is_pinned", "-published_at", "-id")
MANAGEMENT_ORDERING = ("-is_pinned", "-created_at", "-id")
STATUS_FILTERS = ("draft", "scheduled", "published")

CATEGORY_PARAM = OpenApiParameter(
    name="category",
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    required=False,
    enum=list(Announcement.Category.values),
    description="按公告分类筛选；未知分类返回 400。",
)
STATUS_PARAM = OpenApiParameter(
    name="status",
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    required=False,
    enum=list(STATUS_FILTERS),
    description="管理端按发布状态筛选：draft / scheduled / published；未知状态返回 400。",
)


def public_announcements():
    """已发布且可见时间已到的公告；公开列表、公开详情与概览统计共用同一口径。"""
    return Announcement.objects.filter(is_published=True, published_at__lte=timezone.now())


def filter_by_category(queryset, raw):
    """Apply the optional ?category= filter, rejecting values outside the model choices."""
    if raw in (None, ""):
        return queryset
    if raw not in Announcement.Category.values:
        raise ValidationError({"category": [f"Unknown category: {raw}."]})
    return queryset.filter(category=raw)


def filter_by_status(queryset, raw, now):
    """Apply the optional management ?status= filter using the same rules as the public list."""
    if raw in (None, ""):
        return queryset
    if raw == "draft":
        return queryset.filter(is_published=False)
    if raw == "scheduled":
        return queryset.filter(is_published=True, published_at__gt=now)
    if raw == "published":
        return queryset.filter(is_published=True, published_at__lte=now)
    raise ValidationError({"status": [f"Unknown status: {raw}."]})


class IsActiveStaff(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_active and request.user.is_staff)


class CommunityPagination(PageNumberPagination):
    page_size = 20

    def get_paginated_response(self, data):
        return ApiResponse.success(
            data={
                "results": data,
                "count": self.page.paginator.count,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
            }
        )


class EnvelopeMixin:
    def retrieve(self, request, *args, **kwargs):
        return ApiResponse.success(data=self.get_serializer(self.get_object()).data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return ApiResponse.created(data=serializer.data)

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object(), data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return ApiResponse.success(data=serializer.data)

    def destroy(self, request, *args, **kwargs):
        self.perform_destroy(self.get_object())
        return ApiResponse.success()


ERRORS = {400: ERROR_RESPONSE, 401: ERROR_RESPONSE, 403: ERROR_RESPONSE, 404: ERROR_RESPONSE}


@extend_schema_view(
    get=extend_schema(
        tags=["Community"],
        summary="List published announcements",
        parameters=[CATEGORY_PARAM],
        responses={200: PUBLIC_LIST, 404: ERROR_RESPONSE},
    )
)
class PublicAnnouncementListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = PublicAnnouncementSerializer
    pagination_class = CommunityPagination
    filter_backends = [SearchFilter]
    search_fields = ("title", "summary", "body")

    def get_queryset(self):
        queryset = filter_by_category(public_announcements(), self.request.query_params.get("category"))
        return queryset.order_by(*PUBLIC_ORDERING)


@extend_schema_view(
    get=extend_schema(
        tags=["Community"],
        summary="Retrieve a published announcement",
        description="Drafts, scheduled announcements and unknown ids all return 404.",
        responses={200: PUBLIC_DETAIL, **ERRORS},
    )
)
class PublicAnnouncementDetailView(EnvelopeMixin, generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = PublicAnnouncementSerializer

    def get_queryset(self):
        return public_announcements()


@extend_schema_view(
    get=extend_schema(
        tags=["Community"],
        summary="Community overview",
        description="Player and announcement counters for the signed-in player dashboard.",
        responses={200: OVERVIEW_RESPONSE, **ERRORS},
    )
)
class CommunityOverviewView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CommunityOverviewSerializer

    def get(self, request):
        now = timezone.now()
        published = Announcement.objects.filter(is_published=True, published_at__lte=now)
        players = get_user_model().objects
        bound_players = (
            players.filter(Q(socialaccount__provider="microsoft") | Q(microsoft_account__isnull=False))
            .distinct()
            .count()
        )
        payload = {
            "announcements": {
                "published": published.count(),
                "latest_published_at": published.order_by("-published_at")
                .values_list("published_at", flat=True)
                .first(),
            },
            "players": {
                "total": players.count(),
                "active": players.filter(is_active=True).count(),
                "minecraft_bound": bound_players,
            },
            "generated_at": now,
        }
        return ApiResponse.success(data=CommunityOverviewSerializer(payload).data)


@extend_schema_view(
    get=extend_schema(
        tags=["Management"],
        description="Supports `?search=` over title, summary and body (drafts included), "
        "plus `?category=` and `?status=` filters.",
        parameters=[CATEGORY_PARAM, STATUS_PARAM],
        responses={200: ANNOUNCEMENT_LIST, **ERRORS},
    ),
    post=extend_schema(tags=["Management"], responses={201: ANNOUNCEMENT_DETAIL, **ERRORS}),
)
class AnnouncementListCreateView(EnvelopeMixin, generics.ListCreateAPIView):
    permission_classes = [IsActiveStaff]
    serializer_class = AnnouncementSerializer
    pagination_class = CommunityPagination
    filter_backends = [SearchFilter]
    search_fields = ("title", "summary", "body")
    queryset = Announcement.objects.all()

    def get_queryset(self):
        queryset = filter_by_category(super().get_queryset(), self.request.query_params.get("category"))
        queryset = filter_by_status(queryset, self.request.query_params.get("status"), timezone.now())
        return queryset.order_by(*MANAGEMENT_ORDERING)


@extend_schema_view(
    get=extend_schema(tags=["Management"], responses={200: ANNOUNCEMENT_DETAIL, **ERRORS}),
    patch=extend_schema(tags=["Management"], responses={200: ANNOUNCEMENT_DETAIL, **ERRORS}),
    delete=extend_schema(tags=["Management"], responses={200: DELETE_RESPONSE, **ERRORS}),
)
class AnnouncementDetailView(EnvelopeMixin, generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsActiveStaff]
    serializer_class = AnnouncementSerializer
    queryset = Announcement.objects.all()
    http_method_names = ["get", "patch", "delete", "head", "options"]


@extend_schema_view(get=extend_schema(tags=["Management"], responses={200: PLAYER_LIST, **ERRORS}))
class PlayerListView(generics.ListAPIView):
    permission_classes = [IsActiveStaff]
    serializer_class = PlayerSerializer
    pagination_class = CommunityPagination
    filter_backends = [SearchFilter]
    # 新绑定在 allauth SocialAccount（uid / extra_data），旧绑定在 MicrosoftAccount。
    search_fields = (
        "username",
        "email",
        "socialaccount__uid",
        "socialaccount__extra_data__mc_username",
        "microsoft_account__mc_username",
        "microsoft_account__mc_uuid",
    )
    queryset = (
        get_user_model()
        .objects.select_related("microsoft_account")
        .prefetch_related("socialaccount_set")
        .order_by("id")
    )


@extend_schema_view(
    get=extend_schema(tags=["Management"], responses={200: PLAYER_DETAIL, **ERRORS}),
    patch=extend_schema(
        tags=["Management"],
        request=PlayerUpdateSerializer,
        description="Only is_active may be changed. Self, staff and superuser accounts are protected.",
        responses={200: PLAYER_DETAIL, **ERRORS},
    ),
)
class PlayerDetailView(EnvelopeMixin, generics.RetrieveAPIView):
    permission_classes = [IsActiveStaff]
    serializer_class = PlayerSerializer
    queryset = get_user_model().objects.select_related("microsoft_account").prefetch_related("socialaccount_set")

    @transaction.atomic
    def patch(self, request, *args, **kwargs):
        self.queryset = self.queryset.select_for_update()
        player = self.get_object()
        if player.pk == request.user.pk or player.is_staff or player.is_superuser:
            raise PermissionDenied("This account is protected.")
        serializer = PlayerUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        player.is_active = serializer.validated_data["is_active"]
        player.save(update_fields=["is_active"])
        return ApiResponse.success(data=PlayerSerializer(player).data)
