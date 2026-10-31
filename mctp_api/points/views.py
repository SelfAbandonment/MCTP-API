from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.exceptions import NotFound
from rest_framework.filters import SearchFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.views import APIView

from mctp_api.mctp_api_core.response import ApiResponse

from .models import PointAccount
from .serializers import (
    GrantCreateSerializer,
    GrantResultSerializer,
    LeaderboardEntrySerializer,
    ManagePointAccountSerializer,
    MyPointsSerializer,
    PointGrantSerializer,
)
from .services import account_for, grant_points, rank_for, user_queryset

User = get_user_model()


class IsActiveStaff(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_active and request.user.is_staff)


class PointsPagination(PageNumberPagination):
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


def account_payload(account: PointAccount, username: str) -> dict:
    return {
        "user_id": account.user_id,
        "username": username,
        "balance": account.balance,
        "total_granted": account.total_granted,
    }


@extend_schema(tags=["Points"], summary="我的积分")
class MyPointsView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MyPointsSerializer

    def get(self, request):
        account = account_for(request.user)
        recent = account.user.point_grants.select_related("granted_by")[:10]
        data = {
            "account": account_payload(account, request.user.username),
            "rank": rank_for(account),
            "recent_grants": recent,
        }
        return ApiResponse.success(data=MyPointsSerializer(data).data)


@extend_schema(tags=["Points"], summary="我的积分流水")
class MyGrantListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PointGrantSerializer
    pagination_class = PointsPagination

    def get_queryset(self):
        return self.request.user.point_grants.select_related("granted_by").order_by("-created_at", "-id")


@extend_schema(tags=["Points"], summary="积分排行榜")
class LeaderboardView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = LeaderboardEntrySerializer

    def get(self, request):
        accounts = PointAccount.objects.filter(balance__gt=0).select_related("user").order_by("-balance", "id")[:50]
        entries = [
            {
                "rank": index,
                "user_id": account.user_id,
                "username": account.user.username,
                "balance": account.balance,
            }
            for index, account in enumerate(accounts, start=1)
        ]
        return ApiResponse.success(data={"results": LeaderboardEntrySerializer(entries, many=True).data})


@extend_schema(tags=["Management"], summary="管理端玩家积分列表")
class ManagePointAccountListView(generics.ListAPIView):
    permission_classes = [IsActiveStaff]
    serializer_class = ManagePointAccountSerializer
    pagination_class = PointsPagination
    filter_backends = [SearchFilter]
    search_fields = ("username", "email")
    queryset = user_queryset()


@extend_schema(tags=["Management"], summary="发放积分")
class GrantPointsView(APIView):
    permission_classes = [IsActiveStaff]
    serializer_class = GrantCreateSerializer

    def post(self, request):
        serializer = GrantCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        user = User.objects.filter(pk=data["user_id"], is_active=True).first()
        if user is None:
            raise NotFound("resource not found")
        account, grant = grant_points(
            user=user,
            amount=data["amount"],
            reason=data["reason"],
            note=data.get("note", ""),
            granted_by=request.user,
        )
        payload = {
            "account": account_payload(account, user.username),
            "grant": grant,
        }
        return ApiResponse.created(data=GrantResultSerializer(payload).data)
