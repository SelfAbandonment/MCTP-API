# EditorConfig 统一编辑器配置

[EditorConfig](https://editorconfig.org/) 确保所有开发者无论使用什么编辑器，代码风格都保持一致。

## 配置规则

| 文件类型 | 缩进方式 | 缩进大小 | 换行符 | 编码 |
|----------|---------|---------|--------|------|
| 所有文件 | 空格 | 4 | LF | UTF-8 |
| `*.py` | 空格 | 4 | LF | UTF-8 |
| `*.js/ts/json/yaml` | 空格 | 2 | LF | UTF-8 |
| `*.md` | 空格 | 4 | LF | UTF-8（保留尾部空格） |
| `Makefile` | Tab | — | LF | UTF-8 |

## 通用规则

- `insert_final_newline = true` — 文件末尾自动添加空行
- `trim_trailing_whitespace = true` — 自动删除行尾多余空格（Markdown 除外）

## 支持的编辑器

- **VS Code** — 安装 [EditorConfig 扩展](https://marketplace.visualstudio.com/items?itemName=editorconfig.editorconfig)（项目已在推荐扩展中）
- **JetBrains (PyCharm)** — 内置支持
- **Vim/Neovim** — 安装 editorconfig 插件

> `.editorconfig` 文件已提交到仓库，拉取代码后自动生效，无需手动配置。
