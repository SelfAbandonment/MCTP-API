# 安全策略

## 支持的版本

| 分支 / 版本 | 状态 |
| --- | --- |
| `main`（生产，Coolify 部署） | ✅ 接受修复 |
| `develop` | ⚠️ 预发布，仅测试用途 |
| 其他分支 | ❌ 不保证 |

## 报告漏洞

请不要在公开 issue、讨论区或 PR 中披露漏洞细节。任选一种方式：

1. GitHub 私密报告：https://github.com/SelfAbandonment/MCTP-API/security/advisories/new
2. 邮件：205823393@qq.com，标题加 `[SECURITY]`

报告里请包含：影响范围、复现步骤、最小验证请求、可能的修复方向。

我们会在 3 个工作日内确认收到；修复并发布后再公开细节。

## 重点关注

- 认证与会话：JWT 签发/刷新、allauth 回调、微软 OAuth
- 越权访问：管理员接口、玩家数据读写边界
- CORS / CSRF / ALLOWED_HOSTS 配置
- 注入类问题与不安全反序列化
- 密钥、`.env`、服务器凭据泄露
- 依赖漏洞（Dependabot 会开 PR）

## 不在范围

- 需要物理接触服务器的问题
- 已在 Dependabot PR 中处理的依赖告警
- 仅影响本地开发环境的配置差异
