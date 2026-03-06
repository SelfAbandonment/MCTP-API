# Git 工作流

## 分支策略

```
main (受保护) ← PR 合并 ← develop (开发) ← feat/xxx, fix/xxx (功能分支)
```

- **`main`** — 受保护的主分支，仅通过 PR 合并，代表稳定发布版本
- **`develop`** — 开发分支，日常开发在此进行，CI 通过才能推送
- **功能分支** — 从 `develop` 创建，开发完成后提 PR 合并回 `develop`

## 日常开发流程

```bash
# 1. 拉取最新 develop
git checkout develop
git pull origin develop

# 2. 创建功能分支
git checkout -b feat/user-auth

# 3. 开发并提交
git add .
git commit -m "feat: 添加用户认证功能"

# 4. 推送并创建 PR
git push origin feat/user-auth
# 去 GitHub 创建 Pull Request → develop
```

## PR 合并流程

1. 推送功能分支到 GitHub
2. 创建 Pull Request → `develop`
3. CI 自动运行 (lint + test)
4. 至少 1 人 Code Review 通过
5. 合并到 `develop`
6. `develop` 稳定后，PR 合并到 `main` (发版)

## 保护规则

| 分支 | 直接推送 | 强制推送 | 删除 | 要求 PR | 要求 CI |
|------|---------|---------|------|--------|--------|
| main | ❌ | ❌ | ❌ | ✅ (1人审核) | ✅ |
| develop | ✅ | ❌ | ❌ | ❌ | ✅ |
