## 改了什么

<!-- 一两句话说明动机和结果，不要写“优化代码”这类空话 -->

Closes #

## 变更类型

- [ ] feat 新功能
- [ ] fix 修复
- [ ] refactor 重构
- [ ] docs 文档
- [ ] test 测试
- [ ] chore 构建 / 依赖 / CI

## 影响面

- [ ] 接口契约（新增 / 修改 / 删除）
- [ ] 认证 / 权限 / CORS
- [ ] 数据模型 / 迁移
- [ ] 部署 / 环境变量
- [ ] CI 或 Jenkinsfile
- [ ] 仅文档

## 验证证据

<!-- 贴命令输出或请求响应摘要；没跑就写“未验证”并说明原因 -->

- [ ] `uv run ruff check .` 通过
- [ ] `uv run ruff format --check .` 通过
- [ ] `uv run python manage.py test --verbosity=2` 通过
- [ ] `uv run python manage.py check` 通过
- [ ] `/api/schema/` 可生成且变更符合预期
- [ ] 手工调用接口验证（贴请求 / 响应摘要，脱敏）

## 回滚方式

<!-- revert 本 PR / 回滚镜像；涉及迁移时必须说明 down 路径或数据修复方案 -->

## Review 重点

<!-- 希望 reviewer 重点看什么，没有就删掉这一节 -->
