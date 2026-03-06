# Commit 提交规范

## 格式

```
类型: 描述（不超过50字）
```

## 支持的类型

| 类型 | 说明 | 示例 |
|------|------|------|
| `feat` | 新功能 | `feat: 添加用户登录接口` |
| `fix` | Bug 修复 | `fix: 修复密码验证逻辑` |
| `docs` | 文档变更 | `docs: 更新 API 文档` |
| `style` | 代码格式 | `style: 格式化 views.py` |
| `refactor` | 代码重构 | `refactor: 重构认证模块` |
| `test` | 测试相关 | `test: 添加登录单元测试` |
| `chore` | 构建/工具 | `chore: 更新依赖版本` |

## 自动校验

项目已配置 `pre-commit` hooks，提交时会自动校验格式：

```bash
# 安装 hooks（仅需一次）
pre-commit install
pre-commit install --hook-type commit-msg
```

不符合规范的提交会被自动拦截。
