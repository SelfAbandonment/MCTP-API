# 微软（Minecraft 正版）OAuth 接入配置指南

本指南手把手带你完成 **Azure AD 应用注册** 和 **本项目 .env 配置**，最终实现"用微软账号登录 → 自动拿到 MC 玩家 UUID/用户名"。

> 适用范围：MCTP-API。Microsoft 授权 → Xbox Live → XSTS → Minecraft Services → MC Profile，共 5 个上游请求，全部在后端完成。

---

## 一、注册 Azure AD 应用

### 1. 进入 Azure 门户
访问 https://portal.azure.com → 用任意微软账号（个人/Outlook 账号即可）登录。免费，不需要 Azure 订阅。

### 2. 打开 App registrations
顶部搜索栏输入 **"App registrations"** 或 **"应用注册"** → 点进去 → **+ New registration**。

### 3. 填写表单

| 字段 | 填什么 |
|---|---|
| **Name** | `MCTP Minecraft Login`（随便起，用户能看到） |
| **Supported account types** | 选 **"Personal Microsoft accounts only"**（最简单，仅个人微软账号） |
| **Redirect URI** | Platform 选 **Web**，URL 填部署后的 API 地址加 `/accounts/microsoft/login/callback/`（allauth 回调） |

> ⚠️ **本地调试**：再加一个 redirect `http://localhost:8000/accounts/microsoft/login/callback/`（在 Authentication 页可加多个）。
> ⚠️ **必须 HTTPS**（除 localhost），所以生产 API 域名先上 HTTPS。
> ⚠️ 旧的 `/api/v1/auth/microsoft/callback/` 已移除，Azure 上的旧 URI 可以删掉。

点 **Register** 提交。

### 4. 拿到 Client ID
注册成功后跳到应用 Overview 页，复制 **Application (client) ID**（形如 `f9a1c0d2-1234-5678-90ab-cdef12345678`）。

### 5. 创建 Client Secret
左侧菜单 → **Certificates & secrets** → **+ New client secret** → 描述写 `MCTP backend` → 过期时间选 **24 months**（最长）→ Add。

⚠️ **立即复制** `Value` 列的值（形如 `aBc7Q~xxxxxx...`），离开页面后再也看不到。这就是 `MS_CLIENT_SECRET`。

### 6. 配置 API 权限（很重要）
左侧菜单 → **API permissions** → 默认会有一个 `User.Read`，**不需要 Xbox 权限**（Xbox Live token 是后端用 Microsoft access_token 换的，scope 在代码里指定）。直接关闭即可。

### 7.（可选）配 Logo & 同意页文案
**Branding & properties** 里上传 logo、填发布者名称，登录授权页会显示，体验更好。

---

## 二、本项目环境变量

在 `MCTP-API/.env`（本地）和 **Coolify 环境变量面板**（生产）添加：

```bash
# ==== django-allauth / Microsoft ====
MS_CLIENT_ID=f9a1c0d2-1234-5678-90ab-cdef12345678
MS_CLIENT_SECRET=aBc7Q~xxxxxx
# Azure 的 Redirect URI 使用 allauth 回调（见上），无需 MS_REDIRECT_URI
# 登录成功后浏览器的落点（Vue hash 路由，必须带 #）
FRONTEND_OAUTH_CALLBACK=https://<your-frontend-domain>/#/auth/microsoft/callback
FRONTEND_BASE_URL=https://<your-frontend-domain>
# SPA 与 API 不同端口时的跨域 / CSRF 白名单
CORS_ALLOWED_ORIGINS=https://<your-frontend-domain>
CSRF_TRUSTED_ORIGINS=https://<your-frontend-domain>
# 用于加密存储 ms_refresh_token，生成方式: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
MS_TOKEN_FERNET_KEY=填写生成的 fernet key
```

> 本地开发用 `http://localhost:8000/accounts/microsoft/login/callback/` 和 `http://localhost:5173/#/auth/microsoft/callback`，且前端建议用 `http://localhost:5173`（不要和 API 的 `127.0.0.1` 混用，否则 session/CSRF cookie 不同域）。生产环境请使用实际部署域名，不要直接复制示例占位符。

---

## 二·五、认证架构（allauth headless）

- 账户、密码登录、注册、Microsoft 社交登录全部由 **django-allauth** 接管：
  - 浏览器接口：`/_allauth/browser/v1/...`（session cookie + CSRF）
  - 自定义 Microsoft provider：`mctp_api/auth/microsoft_provider/`，使用 `login.live.com` + `XboxLive.signin` scope，内部继续走 Xbox/XSTS/Minecraft 链路。
- 前端登录成功后调用 `POST /api/v1/auth/token/session/`，用 allauth session 换取 SimpleJWT，后续 `/api/v1/` 仍用 Bearer Token。
- 旧的自定义 `/api/v1/auth/microsoft/login|callback/` 已移除；旧 `MicrosoftAccount` 表仅作为历史数据保留，不再写入。

---

## 三、上游 token 流程速查

| # | 用啥 | 调谁 | 拿到啥 |
|---|---|---|---|
| 1 | `code` | `https://login.live.com/oauth20_token.srf` | Microsoft `access_token` |
| 2 | MS access_token | `https://user.auth.xboxlive.com/user/authenticate` | Xbox Live token + `uhs` |
| 3 | XBL token | `https://xsts.auth.xboxlive.com/xsts/authorize` | XSTS token |
| 4 | XSTS token + uhs | `https://api.minecraftservices.com/authentication/login_with_xbox` | Minecraft `access_token` |
| 5 | MC access_token | `https://api.minecraftservices.com/minecraft/profile` | `{ id: UUID, name: 用户名 }` |

代码实现见 `mctp_api/auth/microsoft.py`。

---

## 四、常见错误码

| 错误 | 原因 | 处理 |
|---|---|---|
| XSTS `2148916233` | 微软账号没有 Xbox profile | 提示用户去 https://xbox.com 创建一个 profile |
| XSTS `2148916235` | 国家/地区禁用 Xbox Live | 提示更换账号或区域 |
| XSTS `2148916238` | 未成年账号需家长同意 | 提示走家长账户流程 |
| MC profile 404 | 该微软账号未购买 Minecraft | 提示"该账号未拥有 Minecraft 正版" |
| `redirect_uri_mismatch` | Azure 配的 URI 和后端发起的不一致 | 完全相同（含尾斜杠/端口） |

---

## 五、安全注意事项

1. **`MS_CLIENT_SECRET` 不进 git**，只走环境变量
2. **`ms_refresh_token` 加密存 DB**，用 `cryptography.Fernet`，密钥也走环境变量
3. **`state` 参数**：发起 OAuth 时生成随机字符串，回调校验，防 CSRF
4. **redirect_uri 严格匹配** Azure 后台配置
