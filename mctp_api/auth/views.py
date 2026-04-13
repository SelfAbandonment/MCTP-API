"""
用户认证视图
"""

from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from mctp_api.auth.serializers import ChangePasswordSerializer, RegisterSerializer, UserSerializer, UserUpdateSerializer
from mctp_api.mctp_api_core.response import ApiResponse


class RegisterView(APIView):
    """用户注册"""

    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(
        summary="用户注册",
        description="创建新用户账号，返回用户信息（不含密码）",
        request=RegisterSerializer,
        responses={
            201: {
                "type": "object",
                "properties": {
                    "code": {"type": "integer"},
                    "message": {"type": "string"},
                    "data": {"type": "object"},
                },
            },
            400: {
                "type": "object",
                "properties": {
                    "code": {"type": "integer"},
                    "message": {"type": "string"},
                    "data": {"type": "object"},
                },
            },
        },
        tags=["认证"],
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return ApiResponse.error(
                message="validation error",
                code=400,
                data=serializer.errors,
                status=400,
            )
        user = serializer.save()
        return ApiResponse.created(
            data=UserSerializer(user).data,
            message="user registered successfully",
        )


class MeView(APIView):
    """当前用户信息"""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="获取当前用户信息",
        description="返回已认证用户的个人资料",
        responses={
            200: {
                "type": "object",
                "properties": {
                    "code": {"type": "integer"},
                    "message": {"type": "string"},
                    "data": {"type": "object"},
                },
            },
        },
        tags=["认证"],
    )
    def get(self, request):
        return ApiResponse.success(data=UserSerializer(request.user).data)

    @extend_schema(
        summary="更新当前用户信息",
        description="更新已认证用户的 username 或 email",
        request=UserUpdateSerializer,
        responses={
            200: {
                "type": "object",
                "properties": {
                    "code": {"type": "integer"},
                    "message": {"type": "string"},
                    "data": {"type": "object"},
                },
            },
            400: {
                "type": "object",
                "properties": {
                    "code": {"type": "integer"},
                    "message": {"type": "string"},
                    "data": {"type": "object"},
                },
            },
        },
        tags=["认证"],
    )
    def put(self, request):
        serializer = UserUpdateSerializer(
            request.user,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        if not serializer.is_valid():
            return ApiResponse.error(
                message="validation error",
                code=400,
                data=serializer.errors,
                status=400,
            )
        serializer.save()
        return ApiResponse.success(
            data=UserSerializer(request.user).data,
            message="user updated successfully",
        )


class ChangePasswordView(APIView):
    """修改密码"""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="修改密码",
        description="修改当前已认证用户的密码，需提供旧密码验证",
        request=ChangePasswordSerializer,
        responses={
            200: {
                "type": "object",
                "properties": {
                    "code": {"type": "integer"},
                    "message": {"type": "string"},
                    "data": {"type": "object"},
                },
            },
            400: {
                "type": "object",
                "properties": {
                    "code": {"type": "integer"},
                    "message": {"type": "string"},
                    "data": {"type": "object"},
                },
            },
        },
        tags=["认证"],
    )
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return ApiResponse.error(
                message="validation error",
                code=400,
                data=serializer.errors,
                status=400,
            )
        serializer.save()
        return ApiResponse.success(message="password changed successfully")
