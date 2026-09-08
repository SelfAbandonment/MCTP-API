# JWT 认证说明

项目使用 SimpleJWT 实现 Bearer Token 认证。

## 认证流程

1. `POST /api/v1/auth/token/` 使用用户名和密码登录。
2. 在请求头中携带 `Authorization: Bearer <access-token>`。
3. access token 过期后，调用 `POST /api/v1/auth/token/refresh/`。

## Token 配置

| 配置项 | 当前值 | 说明 |
|--------|--------|------|
| Access Token 有效期 | 2 小时 | 用于访问受保护接口 |
| Refresh Token 有效期 | 7 天 | 用于刷新 access token |
| Refresh Token 轮换 | 开启 | 刷新时返回新的 refresh token |
| 轮换后黑名单 | 开启 | 旧 refresh token 不能重复使用 |
| 修改密码 | 吊销已有 refresh token | 需要重新登录 |

## 获取 Token

```http
POST /api/v1/auth/token/
Content-Type: application/json
```

```json
{
    "username": "testuser",
    "password": "your_password"
}
```

```json
{
    "access": "<access-token>",
    "refresh": "<refresh-token>"
}
```

## 刷新 Token

```http
POST /api/v1/auth/token/refresh/
Content-Type: application/json
```

```json
{
    "refresh": "<refresh-token>"
}
```

## 公开接口

- `GET /api/v1/health/`
- `POST /api/v1/auth/register/`
- `POST /api/v1/auth/token/`
- `POST /api/v1/auth/token/refresh/`
- Microsoft OAuth 登录和回调接口（回调通过 session state 校验）

## 安全要求

- 生产环境必须使用 HTTPS。
- 不要把 access token、refresh token 或 client secret 写入日志、Issue 或仓库。
- 前端应在 access token 过期时使用 refresh token；refresh token 轮换失败时需要重新登录。
