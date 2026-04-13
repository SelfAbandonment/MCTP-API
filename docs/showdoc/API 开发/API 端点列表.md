# API 端点列表

## 当前可用端点

### 基础接口

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| `GET` | `/api/v1/health/` | 健康检查 | ❌ 不需要 |
| `GET` | `/api/v1/health/detail/` | 详细健康检查（含组件状态） | ✅ 需要 |

### 认证接口

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| `POST` | `/api/v1/auth/register/` | 用户注册 | ❌ 不需要 |
| `POST` | `/api/v1/auth/token/` | 获取 JWT Token（登录） | ❌ 不需要 |
| `POST` | `/api/v1/auth/token/refresh/` | 刷新 Access Token | ❌ 不需要 |
| `GET` | `/api/v1/auth/me/` | 获取当前用户信息 | ✅ 需要 |
| `PUT` | `/api/v1/auth/me/` | 更新当前用户信息 | ✅ 需要 |
| `POST` | `/api/v1/auth/password/` | 修改密码 | ✅ 需要 |

### 文档接口

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/docs/` | Swagger UI 交互式文档 |
| `GET` | `/api/redoc/` | ReDoc 文档 |
| `GET` | `/api/schema/` | OpenAPI 3.0 Schema (YAML) |

### 管理后台

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/admin/` | Django 管理后台 |

---

## 接口响应示例

### 健康检查

```
GET /api/v1/health/
```

```json
{
    "code": 200,
    "message": "service is running",
    "data": {
        "status": "healthy",
        "version": "1.0.0"
    }
}
```

### 用户注册

```
POST /api/v1/auth/register/
```

```json
{
    "username": "testuser",
    "email": "test@example.com",
    "password": "StrongPass123!",
    "password_confirm": "StrongPass123!"
}
```

### 修改密码

```
POST /api/v1/auth/password/
Authorization: Bearer <access_token>
```

```json
{
    "old_password": "OldPass123!",
    "new_password": "NewPass456!",
    "new_password_confirm": "NewPass456!"
}
```

响应：

```json
{
    "code": 200,
    "message": "password changed successfully",
    "data": null
}
```

---

## 扩展新接口

在对应 app 的 `views.py` 中添加视图，在 `urls.py` 中注册路由：

```python
# views.py
from rest_framework.views import APIView
from mctp_api.mctp_api_core.response import ApiResponse

class MyView(APIView):
    def get(self, request):
        return ApiResponse.success(data={"key": "value"})

# urls.py
urlpatterns = [
    path("my-endpoint/", MyView.as_view(), name="my-endpoint"),
]
```

> 💡 更详细的接口文档请访问 `/api/docs/` (Swagger UI)，支持在线测试。
