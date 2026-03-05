# 贡献指南

感谢你对 MCTP-API 项目的关注！以下是参与贡献的流程和规范。

## 🔀 工作流程

1. **Fork** 本仓库（外部贡献者）或直接从 `develop` 创建分支（团队成员）
2. 创建功能分支：`git checkout -b feat/你的功能名 develop`
3. 开发并提交代码
4. 推送分支并创建 **Pull Request** → `develop`
5. 等待 CI 通过 + Code Review
6. 合并到 `develop`

## 🌿 分支命名规范

| 类型 | 格式 | 示例 |
|------|------|------|
| 新功能 | `feat/功能名` | `feat/user-auth` |
| Bug 修复 | `fix/bug描述` | `fix/login-error` |
| 文档 | `docs/描述` | `docs/api-readme` |
| 重构 | `refactor/描述` | `refactor/settings` |
| 紧急修复 | `hotfix/描述` | `hotfix/critical-bug` |

## 📝 Commit 规范

提交信息必须符合 [Conventional Commits](https://www.conventionalcommits.org/) 格式：

```
类型: 描述（不超过50字）
```

**支持的类型：**

| 类型 | 说明 |
|------|------|
| `feat` | 新功能 |
| `fix` | Bug 修复 |
| `docs` | 文档变更 |
| `style` | 代码格式（不影响逻辑） |
| `refactor` | 代码重构 |
| `test` | 测试相关 |
| `chore` | 构建/工具/依赖等 |

## 🛠️ 开发环境设置

### 一键初始化（推荐）

```bash
git clone https://github.com/SelfAbandonment/MCTP-API.git
cd MCTP-API
cp .env.example .env         # 编辑 .env 填入 SECRET_KEY
make setup                   # 自动完成全部初始化
```

> Windows 用户需先安装 make：`choco install make` 或 `winget install GnuWin32.Make`

<details>
<summary>手动初始化（不使用 make）</summary>

```bash
# 1. 克隆并进入项目
git clone https://github.com/SelfAbandonment/MCTP-API.git
cd MCTP-API
git checkout develop

# 2. 创建虚拟环境
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # macOS/Linux

# 3. 安装依赖
pip install -r requirements-dev.txt

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env 填入 SECRET_KEY

# 5. 安装 pre-commit hooks
pre-commit install
pre-commit install --hook-type commit-msg

# 6. 数据库迁移
python manage.py migrate
```

</details>

## ✅ 提交前检查

```bash
make lint          # 代码检查
make format        # 代码格式化
make test          # 运行测试
make check         # Django 系统检查
```

或者手动执行：

```bash
ruff check .
ruff format --check .
python manage.py test
python manage.py check
```

pre-commit hooks 会在提交时**自动执行**以上检查，不通过则无法提交。

## 🔍 Code Review 规范

- 每个 PR 至少需要 **1 人** 审核通过
- CI（lint + test）必须全部通过
- PR 描述需要清晰说明变更内容
- 优先使用 Squash Merge 保持提交历史整洁
