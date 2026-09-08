# API 端点列表

所有 API 均使用 `/api/v1/` 前缀。除特别说明外，错误响应遵循[统一响应格式](统一响应格式.md)。

## 系统接口

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| `GET` | `/api/v1/health/` | 返回最小服务状态，不暴露调试信息 | 不需要 |
| `GET` | `/api/v1/health/detail/` | 检查数据库和应用组件状态 | 需要 |

## 本地账号认证

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| `POST` | `/api/v1/auth/register/` | 注册本地用户 | 不需要 |
| `POST` | `/api/v1/auth/token/` | 用户名密码登录，获取 access/refresh token | 不需要 |
| `POST` | `/api/v1/auth/token/refresh/` | 使用 refresh token 获取新 token | 不需要 |
| `GET` | `/api/v1/auth/me/` | 获取当前用户信息 | 需要 |
| `PUT` | `/api/v1/auth/me/` | 更新当前用户的用户名或邮箱 | 需要 |
| `POST` | `/api/v1/auth/password/` | 修改密码并吊销已有 refresh token | 需要 |

## Microsoft / Minecraft 账号

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| `GET` | `/api/v1/auth/microsoft/login/` | 生成 Microsoft 授权地址；可用于登录或绑定 | 可选 |
| `GET` | `/api/v1/auth/microsoft/callback/` | 接收 Microsoft 回调并跳转前端 | 不需要 |
| `DELETE` | `/api/v1/auth/microsoft/unbind/` | 解绑当前用户的 Microsoft/Minecraft 账号 | 需要 |

完整配置和安全要求见[Microsoft OAuth 配置指南](../../microsoft-oauth-setup.md)。

## 文档与管理后台

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/docs/` | Swagger UI |
| `GET` | `/api/schema/` | OpenAPI 3.0 YAML Schema |
| `GET` | `/admin/` | Django 管理后台 |

## 统一响应示例

### 健康检查

```http
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

### 注册

```http
POST /api/v1/auth/register/
Content-Type: application/json
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

```http
POST /api/v1/auth/password/
Authorization: Bearer <access-token>
Content-Type: application/json
```

修改密码成功后，用户已有的 refresh token 会进入黑名单，需要重新登录。
