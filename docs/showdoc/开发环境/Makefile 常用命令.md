# Makefile 常用命令

项目提供 Makefile 简化常用操作，输入 `make help` 查看所有命令。

## 环境管理

| 命令 | 说明 |
|------|------|
| `make setup` | **一键初始化**：创建虚拟环境 → 安装依赖 → Git Hooks → 数据库迁移 |
| `make venv` | 仅创建虚拟环境 |
| `make install` | 安装生产依赖 |
| `make install-dev` | 安装全部依赖（含开发工具） |

## Django 操作

| 命令 | 说明 |
|------|------|
| `make run` | 启动开发服务器 (`runserver`) |
| `make migrate` | 执行数据库迁移 |
| `make makemigrations` | 生成迁移文件 |
| `make createsuperuser` | 创建超级用户 |
| `make shell` | 进入 Django Shell |
| `make check` | Django 系统检查 |

## 代码质量

| 命令 | 说明 |
|------|------|
| `make lint` | 代码检查 (ruff check) |
| `make format` | 代码格式化 (ruff format + fix) |

## 测试

| 命令 | 说明 |
|------|------|
| `make test` | 运行测试 |
| `make test-v` | 运行测试（详细输出） |

## Git Hooks

| 命令 | 说明 |
|------|------|
| `make hooks` | 安装 pre-commit hooks |
| `make pre-commit` | 手动运行 pre-commit |

## 清理

| 命令 | 说明 |
|------|------|
| `make clean` | 清理 `__pycache__` 和 `.ruff_cache` |

## 文档同步

| 命令 | 说明 |
|------|------|
| `make docs` | 增量同步文档到 ShowDoc（仅推送有改动的） |
| `make docs-force` | 强制全量同步全部文档到 ShowDoc |

## Windows 安装 make（必看）

### 第一步：安装

```powershell
# 方式一：winget（推荐，Windows 11 / 10 自带）
winget install GnuWin32.Make

# 方式二：Chocolatey（需提前安装 choco）
choco install make
```

### 第二步：配置 PATH

> **重要**：GnuWin32 安装后**不会**自动加入系统 PATH，终端会报 `make: 无法识别` 错误。

在 PowerShell 中执行以下命令，将 `make.exe` 所在目录永久写入用户 PATH：

```powershell
$gnuBin = "C:\Program Files (x86)\GnuWin32\bin"
[Environment]::SetEnvironmentVariable("Path", [Environment]::GetEnvironmentVariable("Path", "User") + ";$gnuBin", "User")
```

### 第三步：重启终端

**关闭当前终端（或 VS Code）并重新打开**，环境变量才会生效。

### 验证

```powershell
make --version
# 输出类似 GNU Make 3.81 即表示成功
```

### 常见问题

| 问题 | 解决方案 |
|------|----------|
| `make: 无法识别` | 执行上面的 PATH 配置命令，然后**重启终端** |
| PATH 已配置但仍报错 | 确认路径存在：`Test-Path "C:\Program Files (x86)\GnuWin32\bin\make.exe"` |
| Chocolatey 安装的 make | 路径可能是 `C:\ProgramData\chocolatey\bin`，choco 通常自动加 PATH |
