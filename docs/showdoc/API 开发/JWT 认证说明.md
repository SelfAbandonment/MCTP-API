# JWT 认证说明

项目使用 **SimpleJWT** 实现无状态的 Token 认证。

## 认证流程

```
1. POST /api/v1/auth/token/        ← 登录，获取 access + refresh token
2. 请求头 Authorization: Bearer <access_token>  ← 携带 token 访问接口
3. POST /api/v1/auth/token/refresh/ ← access 过期后用 refresh 换新 token
```

## Token 配置

| 配置项 | 值 | 说明 |
|--------|-----|------|
| Access Token 有效期 | 2 小时 | 用于接口鉴权 |
| Refresh Token 有效期 | 7 天 | 用于刷新 access token |
| 自动轮换 Refresh | 开启 | 刷新时颁发新的 refresh token |
| 黑名单机制 | 开启 | 旧 refresh token 自动失效 |

## 接口说明

### 获取 Token（登录）

```
POST /api/v1/auth/token/
Content-Type: application/json

{
    "username": "admin",
    "password": "your_password"
}
```

**成功响应：**

```json
{
    "access": "eyJhbGciOiJIUzI1NiIs...",
    "refresh": "eyJhbGciOiJIUzI1NiIs..."
}
```

### 刷新 Token

```
POST /api/v1/auth/token/refresh/
Content-Type: application/json

{
    "refresh": "eyJhbGciOiJIUzI1NiIs..."
}
```

### 使用 Token 访问接口

```
GET /api/v1/some-endpoint/
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

## 无需认证的接口

以下接口设置了 `AllowAny` 权限，无需 Token：
- `GET /api/v1/health/` — 健康检查

## 注意事项

- Access Token 过期后**不能续期**，必须用 Refresh Token 换新的
- Refresh Token 使用后会**自动轮换**，旧 Token 立即失效
- 生产环境务必使用 **HTTPS**，防止 Token 被截获
