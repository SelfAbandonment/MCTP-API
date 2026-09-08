# GitHub Actions CI/CD

工作流文件：[`.github/workflows/ci.yml`](../../../.github/workflows/ci.yml)。

## 触发条件

| 事件 | 分支 |
|------|------|
| `push` | `main`、`develop` |
| `pull_request` | 目标为 `main` 或 `develop` |

## 检查阶段

### Lint

使用 `astral-sh/setup-uv@v4` 安装 Python 3.12 依赖，执行：

- `uv run ruff check .`
- `uv run ruff format --check .`

### Test

Lint 通过后执行：

- `uv run python manage.py check`
- `uv run python manage.py test --verbosity=2`

CI 使用非生产 `SECRET_KEY` 和 `DEBUG=False`，不会连接生产数据库。

### Develop 快照构建

目标为 `develop` 的 PR，以及推送到 `develop` 的提交，在 lint 和 test 通过后执行 Docker 构建。镜像使用 commit SHA 标签，仅验证 Dockerfile 和依赖可构建，不推送镜像仓库。

### Production 构建

目标为 `main` 的发布 PR，以及推送到 `main` 的提交，在 lint 和 test 通过后执行生产镜像构建。当前工作流同样不推送镜像；Coolify 监听 `main` 完成部署。

## 发布顺序

```text
功能分支
  → PR develop
  → lint + test + develop 快照
  → 合并 develop
  → 验证 develop
  → PR main
  → lint + test + production 构建
  → 合并 main
  → main push + production 构建
  → Coolify 部署
```

GitHub Actions 缓存后端不是发布依赖；不要在工作流中重新引入未经仓库验证的 `type=gha` Buildx cache 配置。
