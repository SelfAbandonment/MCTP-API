# Git 工作流

> 本文件是分支与合并规则的**唯一真源**。`AGENTS.md`、权限矩阵、各仓库 README 只做摘要；出现冲突时以本文件为准。

## 分支策略

```
main（生产） ← release PR ← develop（集成） ← feat/* fix/* docs/* chore/*
                                   ↑
                     hotfix/* 从 main 切出，修完同时回 main 与 develop
```

- **`main`**：生产分支，只接收来自 `develop` 的 release PR，以及 hotfix 回流；每次合并后打 tag。
- **`develop`**：集成分支，功能分支的合并目标；**禁止直接推送**，必须走 PR + 必需检查。
- **功能分支**：从最新 `develop` 切出，命名 `feat/`、`fix/`、`docs/`、`refactor/`、`test/`、`chore/`。
- **`hotfix/<name>`**：从 `main` 切出，先 PR 回 `main` 发版，再 PR 回 `develop`，防止下次发布把修复带回去。

## 日常开发

```bash
# 1. 同步 develop
git checkout develop
git pull origin develop

# 2. 切功能分支
git checkout -b feat/user-auth

# 3. 提交（Conventional Commits）
git commit -m "feat: 添加用户认证功能"

# 4. 推送并开 PR → develop
git push origin feat/user-auth
```

## PR 合并规则

| 目标分支 | 直接推送 | 强制推送 | 删除分支 | 必需 PR | 必需检查 | 人工审核 |
|---|---|---|---|---|---|---|
| `main` | ❌ | ❌ | ❌ | ✅ | ✅ lint + test + docker | 0 人 |
| `develop` | ❌ | ❌ | ❌ | ✅ | ✅ lint + test | 0 人 |

**为什么审核是 0 人**：单人维护时 GitHub 不允许作者 approve 自己的 PR，要求 1 人审核会把所有 PR 卡死。改用「必需状态检查 + CODEOWNERS」兜底；等出现稳定的第二审核人，再把 `main` 调到 1 人。

**必需检查的名称**来自工作流 job 名，改名会让保护规则静默失效：

- `lint`
- `test`
- `docker`（可选，仅 develop）

## 发布流程

1. `develop` 通过 CI 后开 release PR：`develop → main`，标题 `release: vX.Y.Z`
2. PR 描述写本次变更摘要与回滚方式
3. 合并后打 tag 并推送：`git tag -a vX.Y.Z -m "vX.Y.Z" && git push origin vX.Y.Z`
4. 部署：前端由 GitHub Pages 自动发布，后端由 Coolify 监听 `main` 自动部署
5. 发布后把 `develop` 上的版本号推进（`pyproject.toml` 的 `version`）

## 合并策略

- 统一 **Squash merge**，PR 标题即最终 commit message。
- 合并后删除功能分支。
- 保护分支禁止 force push；需要回滚用 `git revert`，不改写历史。

## CI 分工

| 位置 | 触发 | 负责 |
|---|---|---|
| GitHub Actions `ci.yml` | PR / push 到 `main`、`develop` | lint、test、docker 构建 |
| Jenkins `MCTP-API-CI`（规划中） | push / PR | 与 Actions 同口径的二次验证，结果回写 commit status |

Jenkins 侧还没建任务时，以 GitHub Actions 为准；建好后两边都应通过才能合并。
