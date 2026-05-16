# MCTP-API Agent Guide

本文件给 Hermes / Codex / Claude 等代码智能体使用。进入本仓库后优先阅读本文件。

## 项目定位

- Django 6.0 + Django REST Framework 后端。
- 仓库路径：`/mnt/d/code/MCTP-API`。
- GitHub：`github.com/SelfAbandonment/MCTP-API`。
- 生产部署：Coolify 监听 `main` 分支，当前 API 地址：`http://api.mcreatopla.top:21009`。

## 分支规则

- `develop`：开发分支，所有功能分支合入这里。
- `main`：生产分支，只接收 `develop` 的 release PR。
- 禁止直接向 `main` 推送功能代码。
- 新任务从 `develop` 拉分支：`feat/<name>`、`fix/<name>`、`chore/<name>`。

## 隐私与安全

- Git 作者统一：`MrDai <205823393@qq.com>`，不要暴露真实姓名。
- 禁止提交 `.env`、token、密码、API key、服务器密码。
- 修改认证、OAuth、CORS、ALLOWED_HOSTS、部署配置时必须说明风险和验证方式。
- 输出日志时主动脱敏密钥。

## 常用命令

```bash
# 安装/同步依赖
uv sync --dev

# Django 系统检查
uv run python manage.py check

# 数据库迁移
uv run python manage.py makemigrations
uv run python manage.py migrate

# 测试
uv run python manage.py test --verbosity=2

# Lint / 格式
uv run ruff check .
uv run ruff format --check .
uv run ruff format .

# 本地运行
uv run python manage.py runserver
```

如使用 Makefile，也可以运行：`make test`、`make lint`、`make format`、`make run`。

## 验证要求

- 改 Python/Django 代码：至少运行 `uv run ruff check .` 和相关 `manage.py test`。
- 改配置/部署：运行 `uv run python manage.py check`，并说明部署环境变量影响。
- 改 API：检查 `/api/schema/` 是否仍可生成；必要时同步前端适配任务。
- 不要声称完成，除非命令或服务响应已验证。

## 代码约定

- Python 遵循 PEP8，尽量使用类型提示。
- 统一响应结构在 `mctp_api/mctp_api_core/response.py`。
- 全局异常处理在 `mctp_api/mctp_api_core/exceptions.py`。
- Microsoft OAuth 相关代码在 `mctp_api/auth/microsoft.py` 和 `mctp_api/auth/microsoft_views.py`。
- API 文档由 drf-spectacular 生成，入口：`/api/docs/`、`/api/schema/`。

## 多智能体协作

推荐看板 assignee：

- `backend`：Django/API/认证/测试。
- `frontend`：当前端需要同步接口变更时创建子任务。
- `reviewer`：PR 审查、安全检查、合并前验证。
- `devops`：Docker/Coolify/Gitea/GitHub Actions/服务器。

代码变更任务完成后，如不是微小文档改动，应先 block 为 `review-required` 或创建 reviewer 子任务，不要直接合并。
