# GitHub Actions CI/CD

项目使用 GitHub Actions 实现自动化持续集成，每次推送或提交 PR 时自动运行。

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
| 安装 Python 3.12 | `actions/setup-python@v5` (带 pip 缓存) |
| 安装依赖 | `pip install -r requirements.txt` |
| Django check | 检查项目配置是否正确 |
| Django test | 运行所有单元测试 |

## 流程图

```
Push/PR → Lint (ruff check + format)
              ├── ❌ 失败 → 阻止合并
              └── ✅ 通过 → Test (Django check + test)
                                ├── ❌ 失败 → 阻止合并
                                └── ✅ 通过 → 允许合并
```

## 查看结果

- 进入 GitHub 仓库 → **Actions** 标签页
- 每次推送/PR 都会生成一条运行记录
- 绿色 ✅ 表示通过，红色 ❌ 表示失败，点击查看详细日志
