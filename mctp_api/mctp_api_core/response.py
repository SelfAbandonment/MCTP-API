"""
统一 API 响应格式工具类
"""

from rest_framework.response import Response


class ApiResponse:
    """
    统一 API 响应格式

    成功响应:
    {
        "code": 200,
        "message": "success",
        "data": { ... }
    }

    错误响应:
    {
        "code": 400,
        "message": "错误描述",
        "data": null
    }
    """

    @staticmethod
    def success(data=None, message="success", code=200, status=200):
        return Response(
            {"code": code, "message": message, "data": data},
            status=status,
        )

    @staticmethod
    def error(message="error", code=400, data=None, status=400):
        return Response(
            {"code": code, "message": message, "data": data},
            status=status,
        )

    @staticmethod
    def created(data=None, message="created"):
        return ApiResponse.success(data=data, message=message, code=201, status=201)

    @staticmethod
    def not_found(message="resource not found"):
        return ApiResponse.error(message=message, code=404, status=404)

    @staticmethod
    def unauthorized(message="authentication required"):
        return ApiResponse.error(message=message, code=401, status=401)

    @staticmethod
    def forbidden(message="permission denied"):
        return ApiResponse.error(message=message, code=403, status=403)
