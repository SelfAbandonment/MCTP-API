# API 架构概览

## 技术栈

| 组件 | 技术 | 版本范围 | 说明 |
|------|------|----------|------|
| Web 框架 | Django | `>=6.0,<7.0` | Web 应用与管理后台 |
| REST 框架 | Django REST Framework | `>=3.15,<4.0` | API 视图、认证和序列化 |
| 认证 | SimpleJWT | `>=5.3,<6.0` | Bearer JWT 认证与 refresh token 黑名单 |
| 跨域 | django-cors-headers | `>=4.4,<5.0` | CORS 请求控制 |
| API 文档 | drf-spectacular | `>=0.29,<1.0` | OpenAPI 3.0 Schema 与 Swagger UI |
| 依赖管理 | uv | `uv.lock` | 锁定并同步运行时、开发依赖 |

实际安装版本由 [pyproject.toml](../../../pyproject.toml) 与 [uv.lock](../../../uv.lock) 决定。

## API 版本策略

当前稳定 API 使用 `/api/v1/` 前缀。新增破坏性变更时创建新的版本前缀，不修改既有 v1 契约。

```
/api/v1/       当前 API
/api/v1/auth/  认证 API
/api/docs/     Swagger UI
/api/schema/   OpenAPI Schema（YAML）
```

## 路由组织

```text
mctp_api/
├── urls.py                    # 管理后台、API、JWT 和 OpenAPI 路由
├── settings.py                # Django、DRF、JWT、CORS 和 OAuth 配置
├── auth/
│   ├── urls.py                # 注册、用户资料、密码和 Microsoft OAuth
│   ├── views.py               # 本地账号认证视图
│   ├── microsoft_views.py     # Microsoft OAuth 回调与解绑
│   ├── serializers.py         # 请求校验和用户响应
│   └── microsoft.py           # Microsoft → Xbox → Minecraft 换 token 流程
└── mctp_api_core/
    ├── views.py               # 健康检查接口
    ├── response.py            # 统一响应封装
    └── exceptions.py          # 全局 DRF 异常转换
```

## API 文档入口

| 文档类型 | 地址 | 说明 |
|----------|------|------|
| Swagger UI | `/api/docs/` | 浏览 Schema 并在线发送请求 |
| OpenAPI Schema | `/api/schema/` | 原始 OpenAPI 3.0 YAML 文档 |
