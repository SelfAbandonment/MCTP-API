# Pull Request 模板

每次在 GitHub 创建 PR 时，会自动弹出以下模板，方便描述变更内容：

---

## 模板内容

每个 PR 需要填写：

### 1. 变更说明
简要描述这个 PR 做了什么。

### 2. 关联 Issue
关联的 Issue 编号，例如 `closes #123`（合并后自动关闭 Issue）。

### 3. 变更类型（勾选）
- 🆕 新功能 (feat)
- 🐛 Bug 修复 (fix)
- 📖 文档更新 (docs)
- 🎨 代码格式/样式 (style)
- ♻️ 代码重构 (refactor)
- ✅ 测试相关 (test)
- 🔧 构建/工具链 (chore)

### 4. 自查清单
提交前请确认：
- 代码已通过 `ruff check` 和 `ruff format`
- 已编写/更新相关测试
- 已更新相关文档（如有必要）
- commit message 符合规范
