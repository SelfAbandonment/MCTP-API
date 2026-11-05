# Jenkins 集成

## 当前职责

GitHub Actions 负责全部前后端 CI，详情见 [GitHub Actions CI](GitHub%20Actions%20CI.md)。
Jenkins 只负责生产部署、AstrBot 通知与磁盘治理。

| 任务 | 用途 | 触发 |
|---|---|---|
| `MCTP-Deploy` | `main` 的前端 dist + 后端镜像联合部署 | 两仓库 release workflow 请求 |
| `MCTP-Notify` | AstrBot 通知 | GitHub Actions CI 失败 |
| `MCTP-Cleanup` | 部署工作区磁盘治理 | Jenkins 定时、手动 |

核查时已通过 Jenkins API 核实以上任务。`MCTP-Deploy` 只公开 `BRANCH` 和 `FORCE_DEPLOY` 两个参数；最近检查的部署构建由用户触发，尚不能据此确认 GitHub 自动发布已实际跑通。旧 `MCTP-API-CI`、`MCTP-FE` 多分支 CI 已不在任务列表中。
根 [Jenkinsfile](../../../Jenkinsfile) 仅保留历史实现，不代表 CI 仍在 Jenkins 跑。
不要按旧文档重新添加多分支任务、GitHub webhook 或 Jenkins 必需状态。

## 生产发布接口

- GitHub 仓库需配置 Secret：`JENKINS_URL`、`JENKINS_USER`、`JENKINS_TOKEN`。
- 使用 Jenkins 用户 **API Token**，不是密码；API Token POST 不需要依赖 crumbIssuer。
- 当前 `MCTP-Deploy` 参数只有 `BRANCH` 和 `FORCE_DEPLOY`；workflow 保持这两个参数，不发送不存在的 SHA 参数。
- `BRANCH=main`，部署任务应在 precheck 拒绝其他分支；同任务并发排队，不中止进行中的部署。
- release 从成功的 `main` push CI 完成事件触发，并校验前后端两个当前 `main` SHA 的 push CI 都成功；请求前再次确认两边 SHA 未变。跨仓使用公开 GitHub Actions API；网络错误、限流或无成功 CI 时不会触发部署。
- 手动 GitHub release 也必须选择 `main` 并满足双仓 CI 门禁；从 Jenkins 直接启动的手动构建不经过 GitHub Actions 门禁，操作前需人工确认两仓 CI。
- 自动 POST 无重试且有超时。GitHub 请求成功不代表 Jenkins 部署成功；网络超时时先查队列/构建，再决定是否重试。
- main 合并后必须核对对应部署构建及 API 健康检查。此次未触发部署。

## 已有部署保护与剩余边界

- Jenkins 已在 `precheck` 读取前后端 `main` SHA、按 SHA 对去重，并通过同任务排队避免并行覆盖。
- 任务随后仍按 `BRANCH=main` 检出分支，不是按 `precheck` 记录的 commit 检出。若任一 `main` 在检查后、checkout 前移动，仍存在竞态；要消除它，需使用已记录 SHA checkout。
- GitHub release workflow 会校验两仓对应 SHA 的 CI；Jenkins 的 SHA 对去重与串行队列继续作为第二道保护。
- 核实 SQLite 数据卷、备份、迁移和 staticfiles 收集；CI 镜像构建不能替代这些部署验证。
- Coolify 不应再监听 main 自动部署；此次未访问/修改 Coolify。

本次只修改本地独立工作区，没有更新 Jenkins XML、GitHub 分支保护、Secrets 或生产环境变量。

## 通知

`MCTP-Notify` 接受 `REPO`、`STATUS`、`TITLE`、`BRANCH`、`PR`、`URL`、`DETAILS`。
CI 失败请求通知；fork 无 Secrets 时不尝试。请求失败只记录明确 warning，不改变原 CI 失败结论。
AstrBot 地址、API Key、webhook token 在 Jenkins 凭证中维护，不写入仓库。

## 排查顺序

1. whoami 确认凭证可用，再 list_jobs 确認任务名，不猜任务。
2. get_job/list_builds 看参数和最近构建。
3. 失败时查看构建详情、stage 和 console log；日志输出主动脱敏。
4. 确需触发时再 trigger/wait；未经确认不要重跑生产部署。

401 通常是 Token，403 是权限，404 是任务/构建号；API Token 与登录密码不能混用。
