# PR 自动标签

当有人创建 Pull Request 时，CI 会根据**分支名前缀**自动给 PR 打上对应标签。

## 标签映射规则

| 分支前缀 | 自动标签 | 含义 |
|----------|---------|------|
| `feat/` | `enhancement` | 新功能 |
| `fix/` | `bug` | Bug 修复 |
| `docs/` | `documentation` | 文档更新 |
| `hotfix/` | `bug` + `urgent` | 紧急修复 |
| `refactor/` | `refactor` | 代码重构 |
| `test/` | `test` | 测试相关 |
| `chore/` | `chore` | 构建/工具 |
| `release/` | `release` | 版本发布 |

## 示例

创建分支 `feat/user-auth` 并提 PR → 自动标记为 `enhancement`

> 💡 标签有助于快速筛选和管理 PR，一目了然地看到每个 PR 的类型。
