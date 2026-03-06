# 代码检查配置 (Ruff)

项目使用 [Ruff](https://docs.astral.sh/ruff/) 作为 Python 代码检查和格式化工具，替代传统的 flake8 + black + isort 组合。

## 基本配置

| 配置项 | 值 | 说明 |
|--------|-----|------|
| Python 版本 | 3.12 | 目标 Python 版本 |
| 行宽限制 | 120 字符 | 单行最大长度 |

## 启用的检查规则

| 规则代码 | 来源 | 说明 |
|----------|------|------|
| `E` | pycodestyle | 代码风格错误 |
| `W` | pycodestyle | 代码风格警告 |
| `F` | pyflakes | 逻辑错误（未使用变量、未定义名称等） |
| `I` | isort | import 排序 |
| `B` | flake8-bugbear | 常见 Bug 模式检测 |
| `UP` | pyupgrade | 自动升级到新版 Python 语法 |

## 忽略规则

| 文件 | 忽略 | 原因 |
|------|------|------|
| `*/admin.py` | `F401` (未使用导入) | Django 模板文件，后续开发会使用 |
| `*/models.py` | `F401` | 同上 |
| `*/views.py` | `F401` | 同上 |
| `*/tests.py` | `F401` | 同上 |

## 常用命令

```bash
# 检查代码问题
ruff check .

# 自动修复可修复的问题
ruff check . --fix

# 检查代码格式
ruff format --check .

# 自动格式化
ruff format .
```

> 💡 提交代码时 pre-commit 会**自动运行** ruff check 和 ruff format，无需手动执行。
