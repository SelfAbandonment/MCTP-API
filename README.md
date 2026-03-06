# MCTP-API

MCTP 项目后端 API，基于 Django 6.0 构建。

## 🚀 快速开始

### 一键初始化（推荐）

```bash
git clone https://github.com/SelfAbandonment/MCTP-API.git
cd MCTP-API
cp .env.example .env         # 编辑 .env 填入 SECRET_KEY
make setup                   # 自动创建虚拟环境 + 安装依赖 + Git Hooks + 数据库迁移
make run                     # 启动开发服务器
```

> **Windows 用户需先安装 make**，见下方说明 👇

<details>
<summary>🔧 Windows 安装 make（必看）</summary>

**安装** — 二选一：

```powershell
# 方式一：winget（推荐）
winget install GnuWin32.Make

# 方式二：Chocolatey
choco install make
```

**配置 PATH**（安装后 `make` 仍报"无法识别"时执行）：

```powershell
# 将 GnuWin32 永久加入用户 PATH
$gnuBin = "C:\Program Files (x86)\GnuWin32\bin"
[Environment]::SetEnvironmentVariable("Path", [Environment]::GetEnvironmentVariable("Path", "User") + ";$gnuBin", "User")
```

> 执行后 **关闭并重新打开终端 / VS Code** 才会生效。验证：`make --version`

</details>

<details>
<summary>📋 手动初始化（不使用 make）</summary>

```bash
git clone https://github.com/SelfAbandonment/MCTP-API.git
cd MCTP-API
git checkout develop

# 虚拟环境
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # macOS/Linux

# 安装依赖
pip install -r requirements-dev.txt

# 环境变量
cp .env.example .env
# 编辑 .env 填入 SECRET_KEY

# Git Hooks
pre-commit install
pre-commit install --hook-type commit-msg

# 数据库 & 启动
python manage.py migrate
python manage.py runserver
```

</details>

## 📌 常用命令 (Makefile)

| 命令 | 说明 |
|------|------|
| `make setup` | 一键初始化开发环境 |
| `make run` | 启动开发服务器 |
| `make migrate` | 执行数据库迁移 |
| `make makemigrations` | 生成迁移文件 |
| `make test` | 运行测试 |
| `make lint` | 代码检查 (ruff) |
| `make format` | 代码格式化 (ruff) |
| `make hooks` | 安装 pre-commit hooks |
| `make pre-commit` | 手动运行 pre-commit |
| `make docs` | 同步文档到 ShowDoc（增量） |
| `make docs-force` | 强制全量同步文档到 ShowDoc |
| `make clean` | 清理缓存文件 |

## 🔀 Git 工作流

- **`main`** — 受保护的主分支，仅通过 PR 合并
- **`develop`** — 开发分支，日常开发在此进行
- **功能分支** — 从 `develop` 创建，命名格式：`feat/功能名`、`fix/bug名`

> 详细贡献流程请查看 [CONTRIBUTING.md](CONTRIBUTING.md)

### Commit 规范

提交信息必须符合以下格式：

```
类型: 描述（不超过50字）
```

支持的类型：`feat` | `fix` | `docs` | `style` | `refactor` | `test` | `chore`

### 安装 pre-commit hooks

```bash
pre-commit install
pre-commit install --hook-type commit-msg
```

## 🌐 API 文档

启动服务器后访问：

| 地址 | 说明 |
|------|------|
| [/api/docs/](http://127.0.0.1:8000/api/docs/) | Swagger UI 交互式文档 |
| [/api/redoc/](http://127.0.0.1:8000/api/redoc/) | ReDoc 文档 |
| [/api/schema/](http://127.0.0.1:8000/api/schema/) | OpenAPI 3.0 Schema |

## �️ 开发环境统一配置

| 配置文件 | 作用 |
|----------|------|
| `.editorconfig` | 统一缩进（4空格）、换行符（LF）、编码（UTF-8） |
| `.python-version` | 锁定 Python 3.12（pyenv 自动识别） |
| `Makefile` | 常用命令快捷方式 |
| `.vscode/settings.json` | VS Code 保存自动格式化 + Ruff 配置 |
| `.vscode/extensions.json` | 推荐扩展（Ruff、Python、EditorConfig 等） |
| `.pre-commit-config.yaml` | 提交时自动检查代码规范和 commit 格式 |

> 打开项目时 VS Code 会自动提示安装推荐扩展

## 📁 项目结构
├── mctp_api/                  # 项目配置
│   ├── settings.py            # Django 设置
│   ├── urls.py                # 主路由（API v1 + 认证 + 文档）
│   └── mctp_api_core/         # 核心应用
│       ├── views.py           # API 视图
│       ├── urls.py            # 子路由
│       ├── models.py          # 数据模型
│       ├── response.py        # 统一响应格式
│       └── exceptions.py      # 全局异常处理
├── requirements.txt           # 生产依赖
├── requirements-dev.txt       # 开发依赖
├── .env.example               # 环境变量模板
├── .editorconfig              # 编辑器统一配置
├── .python-version            # Python 版本锁定
├── pyproject.toml             # 项目元数据 + Ruff 配置
├── .pre-commit-config.yaml    # Git Hooks 配置
├── .vscode/                   # VS Code 团队配置
│   ├── settings.json          # 格式化 / Lint 配置
│   └── extensions.json        # 推荐扩展
└── .github/workflows/         # GitHub Actions CI/CD
    ├── ci.yml                 # Lint + Test
    └── auto-label.yml         # PR 自动标签
```

## 📜 License

MIT License
