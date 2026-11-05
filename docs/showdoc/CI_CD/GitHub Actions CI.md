# GitHub Actions CI/CD

工作流：[ci.yml](../../../.github/workflows/ci.yml)、[release.yml](../../../.github/workflows/release.yml)。

## 触发与环境

- `push`：`main`、`develop`；PR：目标为 `main`、`develop`；支持手动 CI。
- 同一 ref 新 CI 会取消旧 CI；发布工作流单独排队，不中止已运行的发布请求。
- 默认权限为 `contents: read`，PR 报告 job 额外申请评论权限；通知 job 额外申请 `actions: read` 以判断是否需要发送恢复通知，release 也额外申请 `actions: read`。
- Python **3.12**，`astral-sh/setup-uv@v7`；`uv sync --locked --dev` 和 `UV_LOCKED=true` 确保所有步骤不静默修改锁文件。
- Django job 注入 CI 假 `SECRET_KEY` 与 `DEBUG=False`，在 runner 内使用 SQLite；不读取生产环境。

## 检查阶段

| job | 依赖 | 内容 |
|---|---|---|
| `lint` | 无 | Ruff lint + format |
| `schema` | lint | 未提交迁移检查、OpenAPI 验证、归档已验证 schema |
| `test` | lint | Django check、CI 脚本单测、Django 单测、JUnit、覆盖率门禁 |
| `contract` | schema，仅 PR | 固定 base SHA schema 与已验证 revision schema 的 oasdiff |
| `docker` | lint、test、schema | `develop` push/目标 PR 的镜像构建 |
| `production` | lint、test、schema | `main` push/目标 PR 的镜像构建 |
| `notify` | 上述全部 | 失败时请求 Jenkins AstrBot 通知 |

镜像只构建不推送；未重新引入未经验证的 Buildx `type=gha` 缓存。

### 测试与覆盖率

- `scripts/tests` 由 `python -m unittest discover -s scripts/tests -v` 显式执行。
- Django 使用 `xmlrunner` 和 `coverage run --source=mctp_api`。
- 失败后仍从存在的 `.coverage` 生成 XML，再检查行覆盖率下限 **85%**；不会因为测试/门禁失败而遗漏可生成的覆盖率报告。
- JUnit/覆盖率归档保留 14 天。同仓 PR 回写实际通过/失败/跳过数与覆盖率；评论按页查找并清理重复标记评论。评论回写失败只产生 warning，不改变 CI 结果；fork 不尝试写评论。

### OpenAPI 契约

- 使用 PR 事件的 `base.sha`，不在运行中拉取最新目标分支改变基线。
- revision 直接复用 `schema` job 已验证的 `schema.yaml`，不再次生成。
- base 独立 worktree 位于本次 runner 临时目录，用 EXIT trap 清理。
- oasdiff 镜像固定 digest。changelog 执行错误直接失败；breaking 返回 1 表示破坏性变更，返回大于 1 表示执行错误。
- 破坏性变更只有经前端确认并加 PR 标签 `allow-breaking` 才放行；fork 同样执行门禁，只不写评论。
- 缺少结果/执行错误时评论明确“不能确认兼容性”，不会伪装成无破坏性变更。
- base、revision、diff 和状态归档 14 天，支持失败复现。
- `allow-breaking` 标签变动后需重跑 CI 才会重新读取标签状态。

## 必需检查与仓库设置

现有 `main`/`develop` 必需检查为 `lint`、`test`、`schema`、`contract`；名称不变。
`docker`/`production` 当前不在分支保护里，但整个 main CI 未成功时不能自动发布。
如希望发布 PR 合并前也必须通过镜像构建，应调整对应目标分支的必需检查，此次未改线上设置。

截至 2026-11-05：两分支有严格检查及管理员约束，审批数为 0；只允许 Squash，合并后自动删分支。
审批要求是否提高需另行决定，不能把 CODEOWNERS 存在误认为强制审批已启用。

## 发布顺序

```text
功能分支 → PR develop → CI + develop 镜像构建
→ 合并 develop → PR main → CI + production 镜像构建
→ 合并 main → main push CI 全部成功
→ release.yml 校验当前 SHA 和最新成功 CI → Jenkins MCTP-Deploy
→ 检查 Jenkins 部署结果与线上健康检查
```

`release.yml` 使用 `workflow_run`，只处理本仓库 `main` push 的成功事件；过时 SHA 跳过。
手动发布必须选 `main`，且当前 SHA 已有成功 push CI；`force_deploy` 不绕过 CI。
GitHub 默认分支是 `develop`，workflow_run 定义须先通过 PR 进入默认分支才生效。
HTTP 有连接/总超时；API Token 鉴权不依赖 crumb，不自动重试可能重复入队的 POST。
成功请求仅表示 Jenkins 接受请求，实际部署结果需要另查。

GitHub Pages 仅是前端预览。**Coolify 不再是生产路径**；仍监听 `main` 时应关闭其自动部署。
Jenkins 已实现两仓 main SHA 读取、SHA 对去重和串行排队；GitHub release workflow 负责双仓 CI 门禁。仍存在 Jenkins precheck 与分支 checkout 间的 SHA 竞态，详见 [Jenkins 集成](Jenkins%20集成.md)。

## 主要配置检查

- [Dockerfile](../../../Dockerfile)：基础解释器与 CI 同为 3.12；依赖从 frozen lock 安装，镜像构建时运行 `collectstatic`，使用 Django `STORAGES` + WhiteNoise manifest；运行时直接执行已安装 gunicorn。
- [dependabot.yml](../../../.github/dependabot.yml)：每周 uv、每月 Actions/Docker；Python major/minor 自动升级暂忽略，解释器升级应联动 CI、Docker 和兼容性验证。
- [.pre-commit-config.yaml](../../../.pre-commit-config.yaml)：Conventional Commit hook 接受 `ci`、`build`、`perf`、`revert` 等仓库使用的类型。
- [.gitignore](../../../.gitignore) 和 [.dockerignore](../../../.dockerignore)：排除环境文件及 CI 报告，保留无密钥的 `.env.example`。
- [settings.py](../../../mctp_api/settings.py)：生产缺少 `SECRET_KEY` 会拒绝启动；启用 OAuth 缺少 Fernet key 也会拒绝启动，行为保持不变。
- 生产还需核实：SQLite 数据持久化/备份、代理头只由受信代理设置、HTTPS Cookie/CORS/CSRF/OAuth 回调一致。
- Django 6 静态文件现通过 `STORAGES` 配置 WhiteNoise manifest，并在 Docker 镜像构建时执行 `collectstatic`；CI 的 Docker job 会覆盖该步骤。生产容器构建需确认实际完成且管理员静态资源可访问。
- [.env.example](../../../.env.example) 不是线上配置真源；此次未读取或修改生产机环境，也未验证线上数据库卷、Cookie 或 Coolify 状态。

## 配套工作流

- `auto-label.yml`：同仓 PR 按分支前缀管理标签；fork 跳过，缺失标签只告警。
- `main`/`develop` push 的 CI 成功、失败都会调用 `MCTP-Notify`，同 ref 只保留最新 run 的通知；PR 与手动运行保留失败/恢复通知，不广播每次成功。通知包含失败 job、commit 与 `ACTOR`（PR 作者或 push/手动运行触发者）。Jenkins 任务需声明并转发 `ACTOR` 为 webhook 的 `actor` 字段，才能使用插件的作者 QQ 映射。缺少 Secret/HTTP 失败显示 warning，不静默吞掉，也不覆盖 CI 原始结果。
- 生产 release workflow 只确认 `MCTP-Deploy` 已接受请求，不代表实际部署结果。开始/成功/失败/回滚通知需由活动 Jenkins `MCTP-Deploy` post actions 调用 `MCTP-Notify`，使用 `EVENT=deploy`；回滚必须由部署任务明确报告。本仓库不包含活动 Jenkins 任务配置。
- fork PR 不使用 Jenkins Secrets，也不发送机器人通知或写 PR 评论；如需支持外部贡献者，必须另行设计不执行不可信代码的安全回写流程。
- Jenkins 不再跑 API CI；保留的根 [Jenkinsfile](../../../Jenkinsfile) 是历史脚本，不要作为活跃任务重新启用。
