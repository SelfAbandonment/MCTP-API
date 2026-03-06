# API 端点列表

## 当前可用端点

### 基础接口

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| `GET` | `/api/v1/health/` | 健康检查 | ❌ 不需要 |

### 认证接口

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| `POST` | `/api/v1/auth/token/` | 获取 JWT Token（登录） | ❌ 不需要 |
| `POST` | `/api/v1/auth/token/refresh/` | 刷新 Access Token | ❌ 不需要 |

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

## 健康检查响应示例

```
GET /api/v1/health/
```

```json
{
    "code": 200,
    "message": "service is running",
    "data": {
        "status": "healthy",
        "version": "1.0.0",
        "debug": true
    }
}
```

## 扩展新接口

在 `mctp_api_core/views.py` 中添加视图，在 `mctp_api_core/urls.py` 中注册路由：

```python
# views.py
from rest_framework.views import APIView
from mctp_api.mctp_api_core.response import ApiResponse

class MyView(APIView):
    def get(self, request):
        return ApiResponse.success(data={"key": "value"})

# urls.py
urlpatterns = [
    path("health/", HealthCheckView.as_view(), name="health-check"),
    path("my-endpoint/", MyView.as_view(), name="my-endpoint"),
]
```

> 💡 更详细的接口文档请访问 `/api/docs/` (Swagger UI)，支持在线测试。
