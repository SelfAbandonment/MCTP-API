# django-allauth 认证接入说明

## 为什么迁移

旧实现自行完成 Microsoft OAuth（`/api/v1/auth/microsoft/*`）并把 JWT 通过 URL 传给前端，存在：

- token 进入浏览器历史/日志的风险；
- 无标准账户体系（注册、密码策略、社交账号解绑、后台管理都靠自研）；
- 绑定模式实际不可用（`authentication_classes=[]` 导致 `request.user` 恒为匿名）。

新实现由 **django-allauth 65.20.1** 接管账户与社交登录，Minecraft 校验保留在自定义 provider 中。

## 架构

```
Vue SPA
  │ 1. 密码登录/注册/微软登录
  ▼
allauth headless browser API  /_allauth/browser/v1/...   (session cookie + CSRF)
  │ 2. 自定义 Microsoft provider（login.live.com, scope: XboxLive.signin offline_access）
  ▼
Xbox Live → XSTS → Minecraft Services → 校验拥有游戏 + 读取 UUID/用户名
  │ 3. allauth 创建/登录 Django User + SocialAccount(provider=microsoft, uid=MC UUID)
  ▼
POST /api/v1/auth/token/session/   (SessionAuthentication)
  │ 4. 用 allauth session 换 SimpleJWT（access + refresh）
  ▼
所有 /api/v1/ 继续使用 Authorization: Bearer <JWT>
```

## 端点

| 用途 | 端点 |
| --- | --- |
| headless 配置 | `GET /_allauth/browser/v1/config` |
| 密码登录 | `POST /_allauth/browser/v1/auth/login` |
| 注册 | `POST /_allauth/browser/v1/auth/signup` |
| 当前会话 | `GET /_allauth/browser/v1/auth/session` |
| 退出 | `DELETE /_allauth/browser/v1/auth/session` |
| 发起微软登录/绑定 | `POST /_allauth/browser/v1/auth/provider/redirect`（form: provider=microsoft, process=login/connect, callback_url） |
| OAuth 回调（Azure 填写） | `GET /accounts/microsoft/login/callback/` |
| 会话换 JWT | `POST /api/v1/auth/token/session/` |
| 解绑 | `DELETE /api/v1/auth/microsoft/unbind/` |

旧的 `/api/v1/auth/microsoft/login|callback/` 已删除。

## 关键配置（`.env`）

```bash
MS_CLIENT_ID=...
MS_CLIENT_SECRET=...
FRONTEND_OAUTH_CALLBACK=http://localhost:5173/#/auth/microsoft/callback
FRONTEND_BASE_URL=http://localhost:5173
CORS_ALLOWED_ORIGINS=http://localhost:5173
CSRF_TRUSTED_ORIGINS=http://localhost:5173
# 可选：加密保存 MS refresh token
MS_TOKEN_FERNET_KEY=...
```

Azure App Registration 的 Redirect URI 必须是：

- 本地：`http://localhost:8000/accounts/microsoft/login/callback/`
- 生产：`https://<api-domain>/accounts/microsoft/login/callback/`

同时应用需支持“个人 Microsoft 账户”，并允许 `XboxLive.signin` scope（消费者 Xbox Live 登录）。

## 数据与迁移

- 旧数据**不迁移**：`MicrosoftAccount` 表保留为历史数据（不再写入），用户重新走一次微软登录即可。
- 新绑定关系存于 `allauth.socialaccount`：
  - `uid` = Minecraft UUID；
  - `extra_data.mc_uuid / mc_username`；
  - `extra_data.ms_refresh_token_enc`（Fernet，密钥来自 `MS_TOKEN_FERNET_KEY`；allauth 默认不保存 SocialToken）。
- 已有密码用户不受影响，可继续登录后在玩家中心绑定微软账号（process=connect）。

## 本地验证

```bash
cd MCTP-API
uv sync
uv run python manage.py migrate
uv run python manage.py runserver 127.0.0.1:8000
# 另开：cd MCTP-FE && npm run dev
# 浏览器用 http://localhost:5173/MCTP-Frontend/#/login
```

前端与 API 必须同一 host（都 `localhost` 或都 `127.0.0.1`），否则 session/CSRF cookie 不会共享。
