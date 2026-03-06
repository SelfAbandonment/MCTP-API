"""
全局异常处理器
统一所有 API 错误响应格式
"""

from rest_framework import status
from rest_framework.exceptions import (
    AuthenticationFailed,
    NotAuthenticated,
    NotFound,
    PermissionDenied,
    ValidationError,
)
from rest_framework.response import Response
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    """
    自定义异常处理器，将所有错误统一为:
    {
        "code": <http_status_code>,
        "message": "<error_message>",
        "data": null | { "field": ["error"] }
    }
    """
    response = exception_handler(exc, context)

    if response is None:
        # 未被 DRF 捕获的异常 (500)
        return Response(
            {"code": 500, "message": "internal server error", "data": None},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # 根据异常类型定制消息
    if isinstance(exc, ValidationError):
        message = "validation error"
        data = response.data
    elif isinstance(exc, NotAuthenticated | AuthenticationFailed):
        message = "authentication required"
        data = None
    elif isinstance(exc, PermissionDenied):
        message = "permission denied"
        data = None
    elif isinstance(exc, NotFound):
        message = "resource not found"
        data = None
    else:
        message = str(exc.detail) if hasattr(exc, "detail") else "error"
        data = None

    response.data = {
        "code": response.status_code,
        "message": message,
        "data": data,
    }

    return response
