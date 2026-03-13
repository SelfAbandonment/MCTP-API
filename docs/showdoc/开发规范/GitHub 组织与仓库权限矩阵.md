# GitHub 组织与仓库权限矩阵

适用组织：`MCREATOPIA`

本文档用于统一组织成员角色、团队权限、仓库权限以及分支保护策略，避免迁移到组织后继续沿用个人仓库式管理。

## 推荐团队

- `owners`：组织与仓库治理团队。建议 1 到 2 人，负责组织设置、仓库设置、规则集、Secrets、Actions、成员管理。
- `backend`：Django API 开发团队，负责 `mctp_api/`、`scripts/`、`manage.py` 等应用代码。
- `docs`：文档与流程维护团队，可选，负责 `docs/`、`README.md`、`CONTRIBUTING.md` 等说明文档。

## 组织角色矩阵

- `Owner`：只给组织创建者和极少数核心管理员。可管理成员、团队、仓库、规则、安全策略和计费。严格控制人数，不给日常开发成员。
- `Member`：普通团队成员。通过 Team 继承仓库权限，不授予组织级管理能力。

## 仓库权限矩阵

仓库：`MCTP-API`

- `owners`：`Admin`。负责仓库设置、分支保护、Secrets、Actions、CODEOWNERS。
- `backend`：`Write`。可推送功能分支、创建 PR、处理应用代码。
- `docs`：`Triage` 或 `Write`。只维护文档时使用 `Triage`，需要直接维护文档分支时使用 `Write`。
- 外部协作者：按需单独授权，优先限时授权，不加入 `owners`。

## 组织默认设置建议

- `Base permissions`：`No access`，防止成员自动获得所有仓库访问权。
- `Repository creation`：仅 `Owner` 或受限开放，避免仓库散乱增长。
- `Repository visibility change`：仅 `Owner`，避免误公开私有仓库。
- `Delete/transfer repository`：仅 `Owner`，降低误操作风险。
- `2FA requirement`：开启，降低组织账号泄露风险。

## 当前组织状态

- `Base permissions`：已调整为 `No access`。
- 成员创建仓库：已关闭公开仓库、私有仓库和通用仓库创建权限。
- 成员创建 Pages：已关闭。
- 成员删除或转移仓库：已关闭。
- 成员修改仓库可见性：已关闭。
- 成员创建 Team：已关闭。
- `owners` Team：已创建，并已对 `MCTP-API` 与 `demo-repository` 赋予 `Admin`。
- `backend` Team：已创建，并已对 `MCTP-API` 赋予 `Write`。
- `docs` Team：已创建，并已对 `MCTP-API` 赋予 `Triage`。
- 经典分支保护：`main` 与 `develop` 已创建，但当前组织为 `GitHub Free`，私有仓库规则处于 `Not enforced`。

## 当前待处理风险

- `2FA requirement` 仍未开启，需要你确认所有成员都能完成 2FA 绑定后再启用。
- 组织当前仍允许成员邀请 outside collaborators，这一项尚未成功收紧。
- 私有仓库分支保护规则已存在，但若不升级到 `GitHub Team` 或 `Enterprise`，GitHub 不会真正强制执行。
- 当前组织内 `hiakuyo` 仍为组织 `admin`；如果不是核心治理角色，建议降为普通 `member`。

## 分支保护建议

### `main`

- 禁止直接推送。
- 禁止 force push。
- 禁止删除分支。
- 必须通过 Pull Request 合并。
- 至少 1 个审核通过。
- 必须通过 CI。
- 开启 `Require code owner review`。
- 推荐 `Squash merge`。

### `develop`

- 可保留给 `owners` 直接推送权限，普通成员不建议直接推送。
- 禁止 force push。
- 禁止删除分支。
- 推荐通过 Pull Request 合并。
- 至少 1 个审核通过。
- 必须通过 CI。
- 推荐开启 `Require code owner review`。

## 当前仓库的 CODEOWNERS

团队已经创建完成，当前仓库应使用如下结构：

```text
* @SelfAbandonment @MCREATOPIA/owners
/.github/ @SelfAbandonment @MCREATOPIA/owners
/docs/ @SelfAbandonment @MCREATOPIA/docs
/scripts/ @SelfAbandonment @MCREATOPIA/backend
/mctp_api/ @SelfAbandonment @MCREATOPIA/backend
/manage.py @SelfAbandonment @MCREATOPIA/backend
```

## 落地顺序

1. 确认你本人在组织内为 `Owner`
2. 保持 `owners`、`backend`、`docs` 三个 Team 作为长期权限骨架
3. 新仓库默认只给 `owners` Team `Admin`，再按需要加开发 Team
4. 升级到 `GitHub Team` 后重新检查 `main` 和 `develop` 的保护规则是否进入 `Enforced`
5. 在成员稳定后评估开启组织级 2FA 要求
