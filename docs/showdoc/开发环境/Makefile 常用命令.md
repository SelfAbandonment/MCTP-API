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

## Windows 安装 make

```bash
# 方式一：Chocolatey
choco install make

# 方式二：winget
winget install GnuWin32.Make
```
