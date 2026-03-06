# Pre-commit Hooks 配置

Pre-commit 是在 `git commit` 时**自动运行的检查**，提交前拦截不规范的代码。

## 安装方式

```bash
pip install pre-commit
pre-commit install
pre-commit install --hook-type commit-msg
```

## 已配置的 Hooks

### 📋 基础检查（提交前运行）

| Hook | 作用 |
|------|------|
| `trailing-whitespace` | 自动删除行尾多余空格 |
| `end-of-file-fixer` | 确保文件末尾有换行符 |
| `check-yaml` | 校验 YAML 文件格式是否合法 |
| `check-added-large-files` | 阻止意外提交大文件 |
| `check-merge-conflict` | 检测未解决的合并冲突标记 |

### 🐍 Python 代码检查（提交前运行）

| Hook | 作用 |
|------|------|
| `ruff` | 检查代码问题并**自动修复** |
| `ruff-format` | **自动格式化**代码 |

### 📝 提交信息校验（写 commit message 时运行）

| Hook | 作用 |
|------|------|
| `conventional-pre-commit` | 校验提交信息是否符合 `类型: 描述` 格式 |

## 工作流程

```
git commit → pre-commit 自动运行
  ├── 代码格式不对？→ 自动修复，需要重新 git add
  ├── commit message 不规范？→ 拦截，提示修改
  └── 全部通过 → 提交成功 ✅
```

## 跳过检查（不推荐）

```bash
git commit --no-verify -m "message"
```
