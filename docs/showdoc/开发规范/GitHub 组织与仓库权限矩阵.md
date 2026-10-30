# GitHub 单仓库权限说明

适用仓库：`SelfAbandonment/MCTP-API`、`SelfAbandonment/MCTP-Frontend`

本文说明单仓库模式下的协作边界、分支保护与代码归属。分支规则以 `docs/showdoc/开发规范/Git 工作流.md` 为准。

## 仓库角色

- 仓库所有者：`SelfAbandonment`，负责仓库设置、分支保护、Secrets、Actions、CODEOWNERS。
- 协作者：按需授予 `Write` 或更低权限，只保留真正需要推送分支的人。
- 外部协作者：尽量少量、按需、可回收。

## 推荐模型

- 单仓库协作，不依赖组织 Team 做权限骨架。
- `main` 只接收 release PR 与 hotfix 回流。
- `develop` 必须走 PR，不再允许直接推送。
- 合并统一 **Squash merge**，PR 标题即最终 commit message。

## 分支保护

### `main`

- 禁止直接推送、force push、删除分支
- 必须通过 Pull Request 合并
- 必需状态检查：`lint`、`test`
- 人工审核：**0 人**（单人维护，作者无法自审）
- `Require code owner review`：关闭，等有稳定第二审核人再开

### `develop`

- 禁止直接推送、force push、删除分支
- 必须通过 Pull Request 合并
- 必需状态检查：`lint`、`test`；前端为 `lint`、`test`、`build`
- 人工审核：0 人
- 保持线性历史（Squash）

## CODEOWNERS

两仓均使用 `CODEOWNERS`（前端在 `.github/CODEOWNERS`，后端在仓库根），全部指向 `@SelfAbandonment`，覆盖源码、CI、依赖与文档目录。

## 落地检查表

1. 两个仓库的 `main`、`develop` 都开启分支保护，规则同上
2. 必需检查的名称与实际 workflow job 名一致（改名会静默失效）
3. Actions 变量：前端 `VITE_API_BASE_URL` 必须是 HTTPS
4. 定期清理协作者与旧 token
