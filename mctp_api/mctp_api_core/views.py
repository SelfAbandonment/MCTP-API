"""
mctp_api_core views
"""

import time
from datetime import UTC, datetime, timezone

from django.conf import settings
from django.db import connections
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny, IsAuthenticated
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
            },
            message="service is running",
        )


class HealthCheckDetailView(APIView):
    """详细服务健康检查接口"""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="详细健康检查",
        description="检查 API 服务及各组件的详细运行状态",
        responses={
            200: {
                "type": "object",
                "properties": {"code": {"type": "integer"}, "message": {"type": "string"}, "data": {"type": "object"}},
            },
            503: {
                "type": "object",
                "properties": {"code": {"type": "integer"}, "message": {"type": "string"}, "data": {"type": "object"}},
            },
        },
        tags=["系统"],
    )
    def get(self, request):
        start_time = time.time()

        components = {}
        critical_healthy = True
        has_degradation = False

        databases = {}
        db_config = settings.DATABASES
        for db_alias in db_config.keys():
            try:
                db_start = time.time()
                db_conn = connections[db_alias]
                with db_conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    cursor.fetchone()
                db_response_time = round((time.time() - db_start) * 1000, 2)
                databases[db_alias] = {
                    "status": "up",
                    "response_time_ms": db_response_time,
                    "engine": db_config[db_alias].get("ENGINE", "unknown"),
                }
            except Exception as e:
                if db_alias == "default":
                    critical_healthy = False
                else:
                    has_degradation = True
                databases[db_alias] = {
                    "status": "down",
                    "error": str(e)[:100],
                    "engine": db_config[db_alias].get("ENGINE", "unknown"),
                }

        components["databases"] = databases

        components["application"] = {
            "status": "up",
            "version": settings.SPECTACULAR_SETTINGS.get("VERSION", "1.0.0"),
            "debug_mode": settings.DEBUG,
        }

        if not critical_healthy:
            overall_status = "unhealthy"
        elif has_degradation:
            overall_status = "degraded"
        else:
            overall_status = "healthy"

        total_response_time = round((time.time() - start_time) * 1000, 2)

        data = {
            "status": overall_status,
            "timestamp": datetime.now(UTC).isoformat(),
            "response_time_ms": total_response_time,
            "components": components,
        }

        if overall_status == "healthy":
            return ApiResponse.success(data=data, message="detailed health check completed")
        else:
            return ApiResponse.error(
                data=data,
                message=f"service status: {overall_status}",
                code=503,
                status=503,
            )
