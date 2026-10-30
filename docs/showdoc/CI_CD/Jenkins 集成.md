# Jenkins 集成

## 目标结构

| 任务 | 类型 | 脚本 | 触发 |
|---|---|---|---|
| `MCTP-API-CI` | Multibranch Pipeline | `Jenkinsfile` | push `develop`/`main`、PR |

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
| `SKIP_DOCKER` | false | 跳过 docker build 验证 |

## 阶段

1. 准备 uv
2. 代码检查：`uv sync --dev`、`ruff check`、`ruff format --check`
3. 单元测试：`manage.py check`、`manage.py test --verbosity=2`（`SECRET_KEY`/`DEBUG` 用 CI 假值）
4. Docker 构建：`docker build` 后立即删除镜像，只验证可构建

## 与 GitHub Actions 的分工

GitHub Actions 仍是主门禁；Jenkins 做同口径复核。两边都通过才合并。若 Jenkins agent 不稳定，可先把 `jenkins/mctp-api` 设为非必需检查。
