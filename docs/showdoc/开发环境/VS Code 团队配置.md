# VS Code 团队配置

项目提交了 `.vscode/settings.json` 和 `.vscode/extensions.json`，打开项目后**自动生效**。

## 推荐扩展

打开项目时 VS Code 会弹窗提示安装：

| 扩展 | 说明 |
|------|------|
| `charliermarsh.ruff` | Ruff 代码检查 + 格式化 |
| `ms-python.python` | Python 语言支持 |
| `editorconfig.editorconfig` | EditorConfig 支持 |
| `eamodio.gitlens` | Git 增强（blame、历史等） |
| `GitHub.copilot` | GitHub Copilot AI 助手 |

## 自动行为

以下行为对所有团队成员**统一生效**：

| 配置 | 效果 |
|------|------|
| 保存时自动格式化 | Ruff 自动格式化 Python 代码 |
| 保存时自动 Fix | Ruff 自动修复可修复的问题 |
| 保存时自动排序 Import | 按规范排列 import 语句 |
| 120 字符标尺线 | 编辑器右侧显示行宽参考线 |
| 自动删除尾部空格 | 保存时清理行尾多余空格 |
| 文件末尾自动换行 | 保存时确保文件以空行结尾 |
| 统一 LF 换行符 | 避免跨平台换行符混乱 |
| UTF-8 编码 | 统一文件编码 |

## 搜索排除

以下目录在 VS Code 搜索中自动排除，避免干扰：

- `.venv/` — 虚拟环境
- `__pycache__/` — Python 缓存
- `.ruff_cache/` — Ruff 缓存
- `db.sqlite3` — 数据库文件

## 个人配置

`.vscode/` 目录只提交 `settings.json` 和 `extensions.json`，其他文件（如 `launch.json`）被 `.gitignore` 忽略，可以自行配置。
