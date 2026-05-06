# ==================== MCTP-API Makefile ====================
# 使用方法: make <命令>
# 依赖管理: uv (https://docs.astral.sh/uv/)
# Windows 用户需要安装 make (choco install make 或 winget install GnuWin32.Make)
# ============================================================

MANAGE = uv run python manage.py

# -------------------- 环境管理 --------------------

.PHONY: sync
sync: ## 同步依赖（包括开发工具）
	uv sync --dev

.PHONY: setup
setup: sync hooks migrate ## 一键初始化开发环境
	@echo "✅ 开发环境初始化完成"

# -------------------- Django --------------------

.PHONY: run
run: ## 启动开发服务器
	uv run python manage.py runserver

.PHONY: migrate
migrate: ## 执行数据库迁移
	$(MANAGE) migrate

.PHONY: makemigrations
makemigrations: ## 生成迁移文件
	$(MANAGE) makemigrations

.PHONY: createsuperuser
createsuperuser: ## 创建超级用户
	$(MANAGE) createsuperuser

.PHONY: shell
shell: ## 进入 Django Shell
	$(MANAGE) shell

.PHONY: check
check: ## Django 系统检查
	$(MANAGE) check

# -------------------- 代码质量 --------------------

.PHONY: lint
lint: ## 代码检查 (ruff)
	uv run ruff check .

.PHONY: format
format: ## 代码格式化 (ruff)
	uv run ruff format .
	uv run ruff check . --fix

.PHONY: lint-fix
lint-fix: format ## format 的别名

# -------------------- 测试 --------------------

.PHONY: test
test: ## 运行测试
	$(MANAGE) test

.PHONY: test-v
test-v: ## 运行测试（详细输出）
	$(MANAGE) test -v 2

# -------------------- Git Hooks --------------------

.PHONY: hooks
hooks: ## 安装 pre-commit hooks
	uv run python -m pre_commit install --overwrite
	uv run python -m pre_commit install --hook-type commit-msg --overwrite
	@git config core.autocrlf false
	@sed -i.bak 's/\r//' .git/hooks/pre-commit .git/hooks/commit-msg 2>/dev/null && rm -f .git/hooks/pre-commit.bak .git/hooks/commit-msg.bak || true

.PHONY: pre-commit
pre-commit: ## 手动运行 pre-commit
	uv run python -m pre_commit run --all-files

# -------------------- 文档同步 --------------------

.PHONY: docs
docs: ## 同步文档到 ShowDoc (增量)
	uv run python scripts/sync_showdoc.py

.PHONY: docs-force
docs-force: ## 强制同步全部文档到 ShowDoc
	uv run python scripts/sync_showdoc.py --force

# -------------------- 清理 --------------------

.PHONY: clean
clean: ## 清理缓存文件
	uv run python -c "import shutil, pathlib; [shutil.rmtree(p) for p in pathlib.Path('.').rglob('__pycache__')]; shutil.rmtree('.ruff_cache', True)"

# -------------------- 帮助 --------------------

.PHONY: help
help: ## 显示帮助信息
	@echo "MCTP-API Available Commands:"
	@echo "---------------------------------------------------------------"
	@echo "  make setup           Init dev environment (uv sync + hooks + migrate)"
	@echo "  make sync            Sync deps (uv sync --dev)"
	@echo "  make run             Start dev server"
	@echo "  make migrate         Run database migrations"
	@echo "  make makemigrations  Generate migration files"
	@echo "  make test            Run tests"
	@echo "  make lint            Lint code (ruff check)"
	@echo "  make format          Format code (ruff format + fix)"
	@echo "  make hooks           Install pre-commit hooks"
	@echo "  make pre-commit      Run pre-commit on all files"
	@echo "  make docs            Sync docs to ShowDoc (incremental)"
	@echo "  make docs-force      Force sync all docs to ShowDoc"
	@echo "  make clean           Clean caches (__pycache__ + .ruff_cache)"
	@echo "  make help            Show this help"

.DEFAULT_GOAL := help
