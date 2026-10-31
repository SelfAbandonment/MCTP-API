pipeline {
    agent any

    options {
        timestamps()
        timeout(time: 20, unit: 'MINUTES')
        disableConcurrentBuilds(abortPrevious: true)
        buildDiscarder(logRotator(numToKeepStr: '10', artifactNumToKeepStr: '2'))
        // 显式 checkout，便于先清理 PR 工作区并加一次重试
        skipDefaultCheckout()
    }

    parameters {
        booleanParam(name: 'ALLOW_BREAKING', defaultValue: false, description: '允许破坏性契约变更（需前端确认）')
    }

    environment {
        SECRET_KEY = 'jenkins-ci-secret-not-for-production'
        DEBUG = 'False'
        // 固定 3.12：不指定时 uv 会挑最新解释器，cryptography 等包没有对应 wheel 时会现场编译失败
        UV_PYTHON = '3.12'
    }

    stages {
        stage('checkout') {
            steps {
                script {
                    // PR 工作区先清空，避免旧工作区导致的空目录/脏文件问题
                    if (env.CHANGE_ID) {
                        deleteDir()
                    }
                }
                retry(2) {
                    checkout scm
                }
            }
        }

        stage('变更检测') {
            steps {
                script {
                    if (env.CHANGE_ID) {
                        def target = env.CHANGE_TARGET ?: 'develop'
                        sh "git fetch --no-tags origin +refs/heads/${target}:refs/remotes/origin/${target}"
                        def files = sh(
                            script: "git diff --name-only origin/${target}...HEAD",
                            returnStdout: true
                        ).trim()
                        def list = files ? files.split('\n') : []
                        def relevant = list.any {
                            it ==~ /^(mctp_api\/.*|pyproject\.toml|uv\.lock|scripts\/contract_report\.py)$/
                        }
                        env.RUN_CONTRACT = relevant ? 'true' : 'false'
                        echo "契约相关变更：${relevant}（共 ${list.size()} 个文件）"
                    } else {
                        env.RUN_CONTRACT = 'false'
                    }
                }
            }
        }

        stage('准备 uv') {
            steps {
                sh '''
                    set -e
                    export PATH="$HOME/.local/bin:$PATH"
                    if ! command -v uv >/dev/null 2>&1; then
                        echo "未找到 uv，安装到用户目录的 .local/bin"
                        curl -LsSf https://astral.sh/uv/install.sh | sh
                    fi
                    uv --version
                '''
            }
        }

        stage('代码检查') {
            steps {
                sh '''
                    set -e
                    export PATH="$HOME/.local/bin:$PATH"
                    uv sync --dev
                    uv run python --version
                    uv run ruff check .
                    uv run ruff format --check .
                '''
            }
        }

        stage('迁移与 Schema 检查') {
            steps {
                sh '''
                    set -e
                    export PATH="$HOME/.local/bin:$PATH"
                    uv run python manage.py makemigrations --check --dry-run
                    uv run python manage.py spectacular --validate --file ./schema.validation.yaml
                    rm -f ./schema.validation.yaml
                '''
            }
        }

        stage('契约兼容检查') {
            when {
                expression { env.RUN_CONTRACT == 'true' }
            }
            steps {
                sh '''
                    set -e
                    export PATH="$HOME/.local/bin:$PATH"
                    BASE_REF="${CHANGE_TARGET:-develop}"
                    BASE_DIR="/tmp/mctp-contract-base-${BUILD_NUMBER}"
                    rm -rf "$BASE_DIR"
                    git fetch --no-tags origin "$BASE_REF"
                    git worktree add --detach "$BASE_DIR" FETCH_HEAD
                    ( cd "$BASE_DIR" && uv sync --dev >/dev/null && uv run python manage.py spectacular --file base.yaml )
                    cp "$BASE_DIR/base.yaml" ./base.yaml
                    uv run python manage.py spectacular --file revision.yaml

                    CID="$(hostname)"
                    if ! docker inspect "$CID" >/dev/null 2>&1; then
                        CID="$(grep -oE '[0-9a-f]{64}' /proc/self/cgroup 2>/dev/null | head -1 || true)"
                    fi
                    if [ -n "$CID" ] && docker inspect "$CID" >/dev/null 2>&1; then
                        MOUNT_ARGS="--volumes-from $CID"
                    else
                        MOUNT_ARGS="-v $WORKSPACE:$WORKSPACE"
                    fi

                    docker run --rm $MOUNT_ARGS -w "$WORKSPACE" tufin/oasdiff@sha256:75a513546b09466bfcbb192bd1ed117e5a22945306602ba2a7bbebf2665d1076 \
                        changelog base.yaml revision.yaml --format markdown > contract-changelog.md || true
                    set +e
                    docker run --rm $MOUNT_ARGS -w "$WORKSPACE" tufin/oasdiff@sha256:75a513546b09466bfcbb192bd1ed117e5a22945306602ba2a7bbebf2665d1076 \
                        breaking base.yaml revision.yaml --format markdown > contract-breaking.md
                    status=$?
                    set -e
                    echo "$status" > contract-status.txt
                    git worktree remove --force "$BASE_DIR" || true
                    cat contract-breaking.md
                    if [ "$status" -gt 1 ]; then
                        echo "oasdiff 执行失败（exit $status），请检查镜像/参数/schema"
                        exit 1
                    fi
                    if [ "$status" -eq 1 ] && [ "${ALLOW_BREAKING:-false}" != "true" ]; then
                        echo "检测到破坏性契约变更：请前端确认，或用 ALLOW_BREAKING=true 手动放行"
                        exit 1
                    fi
                    if [ "$status" -eq 1 ]; then
                        echo "检测到破坏性契约变更，ALLOW_BREAKING=true，已放行"
                    fi
                '''
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'contract-*.md,contract-status.txt', allowEmptyArchive: true
            script {
                // 测试/覆盖率/CI 汇总评论由 GitHub Actions 负责；Jenkins 只回写契约评论
                if (env.CHANGE_ID) {
                    withCredentials([usernamePassword(credentialsId: 'github-MCTP', usernameVariable: 'GH_USER', passwordVariable: 'GH_TOKEN')]) {
                        withEnv([
                            "PR_NUMBER=${env.CHANGE_ID}",
                            "GH_REPO=SelfAbandonment/MCTP-API"
                        ]) {
                            sh 'export PATH="$HOME/.local/bin:$PATH"; uv run python scripts/contract_report.py || echo "契约评论失败（不影响构建结果）"'
                        }
                    }
                }
            }
            script {
                // PR 工作区用完即清；uv 缓存位于 $HOME，不受影响
                // 用 env.CHANGE_ID 判断：changeRequest() 在分支构建里也可能返回真值
                if (env.CHANGE_ID) {
                    cleanWs()
                }
            }
        }
        success {
            script {
                // main 通过后自动触发生产部署（MCTP-Deploy 同时构建前后端）
                if (env.BRANCH_NAME == 'main') {
                    echo 'main 构建通过，触发生产部署 MCTP-Deploy'
                    build job: 'MCTP-Deploy', wait: false, parameters: [string(name: 'BRANCH', value: 'main')]
                }
            }
        }
        unsuccessful {
            echo '构建未成功：请检查「代码检查」「迁移与 Schema 检查」「契约兼容检查」阶段日志；测试/覆盖率由 GitHub Actions 负责。'
        }
    }
}
