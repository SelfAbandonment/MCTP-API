# API 架构概览

## 技术栈

| 组件 | 技术 | 版本 | 说明 |
|------|------|------|------|
| Web 框架 | Django | 6.0.3 | Python Web 框架 |
| REST 框架 | Django REST Framework | 3.15.x | RESTful API 构建 |
| 认证 | SimpleJWT | 5.3.x | JWT Token 认证 |
| 跨域 | django-cors-headers | 4.4.x | CORS 跨域支持 |
| API 文档 | drf-spectacular | 0.29.x | OpenAPI 3.0 / Swagger |

## API 版本策略

```
/api/v1/  →  所有 v1 版本接口
/api/v2/  →  未来版本（预留）
```

- URL 路径前缀实现版本控制
- 新版本不影响旧版本的使用
- 废弃接口至少保留一个版本周期

## 目录结构

```
mctp_api/
├── settings.py           # 项目配置（DRF、JWT、CORS 等）
├── urls.py               # 主路由（API v1、认证、文档）
└── mctp_api_core/
    ├── views.py           # API 视图
    ├── urls.py            # 子路由
    ├── models.py          # 数据模型
    ├── response.py        # 统一响应格式
    ├── exceptions.py      # 全局异常处理
    └── admin.py           # 后台管理
```

## 在线文档

| 文档类型 | 地址 | 说明 |
|----------|------|------|
| Swagger UI | `/api/docs/` | 交互式 API 测试界面 |
| ReDoc | `/api/redoc/` | 美观的 API 文档 |
| OpenAPI Schema | `/api/schema/` | 原始 OpenAPI 3.0 Schema (YAML) |
