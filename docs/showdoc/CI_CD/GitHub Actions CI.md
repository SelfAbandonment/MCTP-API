# GitHub Actions CI/CD

工作流文件：[`.github/workflows/ci.yml`](../../../.github/workflows/ci.yml)。

## 触发条件

| 事件 | 分支 |
|------|------|
| `push` | `main`、`develop` |
| `pull_request` | 目标为 `main` 或 `develop` |
| `workflow_dispatch` | 手动重跑 |

同一分支/PR 上重复触发会取消旧的一轮（`concurrency.cancel-in-progress`），工作流只申请 `contents: read`。

## 检查阶段

### Lint（timeout 10 分钟）

使用 `astral-sh/setup-uv@v4` 安装 Python 3.12 依赖，执行：

- `uv run ruff check .`
- `uv run ruff format --check .`

### Test（timeout 15 分钟，依赖 lint）

- `uv run python manage.py check`
- `uv run python manage.py test --verbosity=2`

`SECRET_KEY` 与 `DEBUG` 在 job 级通过 `env` 注入 CI 专用假值，不会连接生产数据库。

### Develop 快照构建（timeout 20 分钟）

目标为 `develop` 的 PR，以及推送到 `develop` 的提交，在 lint 和 test 通过后执行 Docker 构建。镜像使用 commit SHA 标签，只验证 Dockerfile 与依赖可构建，不推送镜像仓库。

### Production 构建（timeout 20 分钟）

目标为 `main` 的发布 PR，以及推送到 `main` 的提交，在 lint 和 test 通过后执行生产镜像构建。同样不推送镜像；Coolify 监听 `main` 完成部署。

## 必需检查

分支保护里应勾选：

- `lint`
- `test`
- `docker`（可选）

job 改名会让分支保护的检查项静默失效，改名前先同步仓库设置。

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

## 配套工作流

- `auto-label.yml`：按分支前缀给 PR 打标签，分支改名时回收旧标签；标签不存在或 fork PR 只告警、不失败。
- `dependabot.yml`：每周一检查 `uv` 依赖与 GitHub Actions，Docker 基础镜像按月检查。
