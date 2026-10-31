# Jenkins 集成

## 目标结构

| 任务 | 类型 | 脚本 | 触发 |
|---|---|---|---|
| `MCTP-API-CI` | Multibranch Pipeline | `Jenkinsfile` | push `develop`/`main`、PR |
| `MCTP-Deploy` | Pipeline | 内联脚本（Jenkins 任务配置） | `MCTP-API-CI` 或 `MCTP-FE` 的 `main` 构建成功后自动触发 |

## 建任务

1. New Item → **Multibranch Pipeline**，名字 `MCTP-API-CI`
2. Branch Sources → GitHub：
   - Repository URL：`https://github.com/SelfAbandonment/MCTP-API.git`
   - Credentials：`github-MCTP`
3. Behaviors：
   - Discover branches，Filter by name：`develop main`
   - Discover pull requests from origin，Strategy：Merging the pull request with the current target branch revision
4. Build Configuration → Script Path：`Jenkinsfile`
5. Scan 触发器：Periodically if not otherwise run → 5 分钟
6. 保存后执行一次 **Scan Repository Now**

## 环境要求

- agent 需要 `docker`（`Docker 构建` 阶段使用）
- 没有 `uv` 时流水线会装到用户目录的 `.local/bin`，需要能访问 `astral.sh`；内网环境请在 agent 上预装 uv

## 状态回写

GitHub Branch Source 会为每个分支和 PR 自动回写两个 status：`continuous-integration/jenkins/branch` 和 `continuous-integration/jenkins/pr-merge`。

注意：这个版本的 `github` 插件没有 `githubNotify` 步骤，脚本里调用会报 `NoSuchMethodError`，所以流水线不自己回写状态。

## 参数

| 参数 | 默认 | 说明 |
|---|---|---|
| `ALLOW_BREAKING` | false | 允许破坏性 OpenAPI 契约变更（需前端确认后手动放行） |

## 阶段

1. checkout：`skipDefaultCheckout` + 显式 `checkout scm`（`retry(2)`）；PR 构建先 `deleteDir()`
2. 准备 uv：确认/安装 `uv`，打印 `uv` 版本
3. 代码检查：`uv sync --dev`、打印 Python 版本、`ruff check`、`ruff format --check`
4. 迁移与 Schema 检查：`makemigrations --check --dry-run`、`spectacular --validate`（schema 生成失败会直接拦下）
5. 契约兼容检查（仅 PR，且改动涉及 `mctp_api/**`、`pyproject.toml`、`uv.lock`）：用 `git worktree` 从目标分支生成 base schema，与当前 revision 用固定 digest 的 `tufin/oasdiff` 比较；破坏性变更失败，`ALLOW_BREAKING=true` 可放行

单元测试、覆盖率（下限 85%）与 JUnit 报告由 GitHub Actions 的 `test` job 负责；Docker 构建也在 GitHub Actions。Jenkins 不再重复这些步骤。

PR 构建结束后自动 `cleanWs()`；`uv` 缓存位于 `$HOME`，不受影响。构建保留 10 条 / 2 份产物；多分支孤儿策略立即清理已关闭 PR；`MCTP-Cleanup` 每周清理旧工作区与 Docker 缓存。

## PR 评论

- **GitHub Actions** 回写 CI 汇总评论：测试通过/失败/跳过数、覆盖率、构建链接（`scripts/ci_report.py`）
- **Jenkins** 回写 API 契约变更评论：是否有破坏性变更、`oasdiff` 变更详情、Jenkins 构建链接（`scripts/contract_report.py`）
- 两者各自带 HTML 标记，重复构建只更新同一条；评论失败不影响构建结果
- 协作者在仓库内分支提的 PR 同样会收到（fork PR 目前不在发现范围内）；Jenkins 凭证需要 Issues 写权限

## 生产部署

- 生产由 `MCTP-Deploy` 负责（前端 dist + 后端镜像），GitHub Pages 只作 `main` 前端预览
- `MCTP-API-CI` 的 `main` 构建成功后自动触发 `MCTP-Deploy`（`BRANCH=main`）
- `MCTP-Deploy` 带 `precheck`，非 `main` 直接失败；并发构建排队而不是中止，避免部署中途被打断
- Coolify 不再是生产部署路径；如仍在监听 `main`，需在 Coolify 侧关闭自动部署

## AstrBot 构建通知

- 需要三个 Jenkins **Secret text** 凭证（Global）：
  - `astrbot-base-url`：`http://<AstrBot-IP>:6185`
  - `astrbot-api-key`：AstrBot OpenAPI Key，scope 含 `plugin`
  - `astrbot-webhook-token`：插件配置里的 `webhook_token`
- 触发：`failure`、`fixed`（上次失败本次恢复）；凭证缺失或网络失败只写日志，不影响构建
- 通知内容：仓库、分支/PR、构建号、耗时、链接，渲染为图片卡片；图片发送失败自动回退纯文本
- 插件源码在 workspace 的 `astrbot-plugins/astrbot_plugin_mctp_ci/`（不在本仓库）

## 与 GitHub Actions 的分工

GitHub Actions 仍是主门禁（分支保护必需检查）；Jenkins 做同口径复核，并在 `main` 成功后承担生产部署。
若 Jenkins agent 不稳定，可先把 `jenkins/mctp-api` 设为非必需检查。
