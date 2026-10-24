from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import SearchFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, BasePermission

from mctp_api.mctp_api_core.response import ApiResponse

from .models import Announcement
from .schemas import (
    ANNOUNCEMENT_DETAIL,
    ANNOUNCEMENT_LIST,
    DELETE_RESPONSE,
    ERROR_RESPONSE,
    PLAYER_DETAIL,
    PLAYER_LIST,
    PUBLIC_LIST,
)
from .serializers import AnnouncementSerializer, PlayerSerializer, PlayerUpdateSerializer, PublicAnnouncementSerializer


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
        responses={200: PUBLIC_LIST, 404: ERROR_RESPONSE},
    )
)
class PublicAnnouncementListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = PublicAnnouncementSerializer
    pagination_class = CommunityPagination

    def get_queryset(self):
        return Announcement.objects.filter(is_published=True, published_at__lte=timezone.now())


@extend_schema_view(
    get=extend_schema(tags=["Management"], responses={200: ANNOUNCEMENT_LIST, **ERRORS}),
    post=extend_schema(tags=["Management"], responses={201: ANNOUNCEMENT_DETAIL, **ERRORS}),
)
class AnnouncementListCreateView(EnvelopeMixin, generics.ListCreateAPIView):
    permission_classes = [IsActiveStaff]
    serializer_class = AnnouncementSerializer
    pagination_class = CommunityPagination
    queryset = Announcement.objects.all().order_by("-created_at", "-id")


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
    search_fields = ("username", "email", "microsoft_account__mc_username", "microsoft_account__mc_uuid")
    queryset = get_user_model().objects.select_related("microsoft_account").order_by("id")


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
    queryset = get_user_model().objects.select_related("microsoft_account")

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
