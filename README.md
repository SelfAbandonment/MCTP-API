# MCTP-API

MCTP 项目后端 API，基于 Django 6.0 构建。

## 🚀 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/SelfAbandonment/MCTP-API.git
cd MCTP-API
git checkout develop
```

### 2. 创建虚拟环境

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
```

### 3. 安装依赖

```bash
# 生产依赖
pip install -r requirements.txt

# 开发依赖（含 ruff、pre-commit 等）
pip install -r requirements-dev.txt
```

### 4. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填入你的 SECRET_KEY 等配置
```

### 5. 数据库迁移 & 启动

```bash
python manage.py migrate
python manage.py runserver
```

## 🔀 Git 工作流

- **`main`** — 受保护的主分支，仅通过 MR 合并
- **`develop`** — 开发分支，日常开发在此进行
- **功能分支** — 从 `develop` 创建，命名格式：`feat/功能名`、`fix/bug名`

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

## 📁 项目结构

```
MCTP-API/
├── manage.py              # Django 管理入口
├── mctp_api/              # 项目配置
│   ├── settings.py        # Django 设置
│   ├── urls.py            # 路由入口
│   └── mctp_api_core/     # 核心应用
│       ├── models.py
│       ├── views.py
│       └── ...
├── requirements.txt       # 生产依赖
├── requirements-dev.txt   # 开发依赖
├── .env.example           # 环境变量模板
├── .github/workflows/     # GitHub Actions CI/CD 配置
└── .pre-commit-config.yaml
```

## 📜 License

MIT License
