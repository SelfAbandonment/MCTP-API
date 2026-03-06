"""
mctp_api_core views
"""

from django.conf import settings
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from mctp_api.mctp_api_core.response import ApiResponse


class HealthCheckView(APIView):
    """服务健康检查接口"""

    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(
        summary="健康检查",
        description="检查 API 服务是否正常运行",
        responses={
            200: {
                "type": "object",
                "properties": {"code": {"type": "integer"}, "message": {"type": "string"}, "data": {"type": "object"}},
            }
        },
        tags=["系统"],
    )
    def get(self, request):
        return ApiResponse.success(
            data={
                "status": "healthy",
                "version": settings.SPECTACULAR_SETTINGS.get("VERSION", "1.0.0"),
                "debug": settings.DEBUG,
            },
            message="service is running",
        )
