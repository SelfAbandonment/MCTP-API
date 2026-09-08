# GitHub Actions CI/CD

项目使用 GitHub Actions 实现自动化持续集成。开发分支会执行快照构建，生产分支会执行生产镜像构建。

## 触发条件

| 事件 | 触发分支 |
|------|---------|
| `push` (代码推送) | `main`、`develop` |
| `pull_request` (PR) | `main`、`develop` |

## 流水线阶段

### 阶段一：Lint（代码检查）

| 步骤 | 说明 |
|------|------|
| 检出代码 | `actions/checkout@v4` |
| 安装 Python 3.12 | `actions/setup-python@v5` (带 pip 缓存) |
| 安装 ruff | 代码检查工具 |
| `ruff check .` | 检查代码问题 |
| `ruff format --check .` | 检查代码格式 |

### 阶段二：Test（测试） — 依赖 Lint 通过

| 步骤 | 说明 |
|------|------|
| 检出代码 | `actions/checkout@v4` |
| 安装 Python 3.12 | `astral-sh/setup-uv@v4` |
| 安装依赖 | `uv sync --dev` |
| Django check | 检查项目配置是否正确 |
| Django test | 运行所有单元测试 |

### 阶段三：Develop 快照构建 — 依赖 Lint 和 Test 通过

目标为 `develop` 的 PR，以及推送到 `develop` 的提交，会构建带有 commit SHA 的 Docker 快照标签。快照不会推送到镜像仓库，只用于验证生产镜像可以构建。

### 阶段四：Production 构建 — 依赖 Lint 和 Test 通过

推送到 `main` 的提交会构建带有 commit SHA 的生产镜像标签。生产部署由 Coolify 监听 `main` 分支执行。

## 流程图

```
Push/PR → Lint (ruff check + format)
              ├── ❌ 失败 → 阻止合并
              └── ✅ 通过 → Test (Django check + test)
                                ├── ❌ 失败 → 阻止合并
                                ├── ✅ 通过 → Develop 快照构建
                                └── ✅ 通过 → 允许合并

Main Push → Lint + Test → Production 构建 → Coolify 部署
```

## 查看结果

- 进入 GitHub 仓库 → **Actions** 标签页
- 每次推送/PR 都会生成一条运行记录
- 绿色 ✅ 表示通过，红色 ❌ 表示失败，点击查看详细日志
