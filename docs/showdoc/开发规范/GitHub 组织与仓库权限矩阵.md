# GitHub 单仓库权限说明

适用仓库：`SelfAbandonment/MCTP-API`

本文档用于说明在单仓库模式下的协作边界、分支保护和代码归属，避免继续沿用组织 Team 模式的配置。

## 仓库角色建议

- 仓库所有者：`SelfAbandonment`，负责仓库设置、分支保护、Secrets、Actions、CODEOWNERS。
- 协作者：按需授予 `Write` 或更低权限，只保留真正需要直接推送分支或参与维护的人。
- 外部协作者：尽量少量、按需、可回收，不使用组织 Team 做权限骨架。

## 当前推荐模型

- 默认以单仓库协作模式为主。
- `main` 用于稳定发布，仅通过 PR 合并。
- `develop` 用于日常集成开发，推荐通过 PR 合并。
- 合并策略使用 `Squash merge`，保持提交历史可读。

## 分支保护建议

### `main`

- 禁止直接推送。
- 禁止 force push。
- 禁止删除分支。
- 必须通过 Pull Request 合并。
- 必须通过 CI。
- 至少 1 个审核通过。
- 是否开启 `Require code owner review` 取决于是否存在稳定的第二审核人。

### `develop`

- 推荐通过 Pull Request 合并。
- 必须通过 CI。
- 是否开启 `Require code owner review` 取决于当前协作者数量和审核流程。
- 保持线性历史，减少回滚成本。

## 当前仓库的 CODEOWNERS

单仓库模式下，建议使用如下结构：

```text
* @SelfAbandonment
/.github/ @SelfAbandonment
/docs/ @SelfAbandonment
/scripts/ @SelfAbandonment
/mctp_api/ @SelfAbandonment
/manage.py @SelfAbandonment
```

## 落地顺序

1. 将本地 `origin` 指回 `SelfAbandonment/MCTP-API`
2. 将文档中的克隆地址统一回个人仓库
3. 将 `CODEOWNERS` 调整为单仓库责任人模式
4. 仅在确认有稳定审核人时再强制开启 `Require code owner review`
5. 定期检查协作者权限，避免长期遗留高权限账号
