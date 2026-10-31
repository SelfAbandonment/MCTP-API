pipeline {
    agent any

    options {
        timestamps()
        timeout(time: 20, unit: 'MINUTES')
        disableConcurrentBuilds(abortPrevious: true)
        buildDiscarder(logRotator(numToKeepStr: '20', artifactNumToKeepStr: '3'))
        // 显式 checkout，便于先清理 PR 工作区并加一次重试
        skipDefaultCheckout()
    }

    parameters {
        booleanParam(name: 'SKIP_DOCKER', defaultValue: false, description: '跳过 docker build 验证')
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

        stage('单元测试与覆盖率') {
            steps {
                sh '''
                    set -e
                    export PATH="$HOME/.local/bin:$PATH"
                    rm -f TEST-*.xml coverage.xml
                    rm -rf htmlcov
                    uv run python manage.py check
                    uv run coverage run --source=mctp_api manage.py test \
                        --testrunner=xmlrunner.extra.djangotestrunner.XMLTestRunner \
                        --verbosity=2
                    uv run coverage report --show-missing
                    uv run coverage xml -o coverage.xml
                    uv run coverage html -d htmlcov
                '''
            }
        }

        stage('Docker 构建') {
            when {
                expression { !params.SKIP_DOCKER }
            }
            steps {
                sh '''
                    set -e
                    IMAGE="mctp-api:jenkins-${BUILD_NUMBER}"
                    docker build -t "$IMAGE" .
                    docker image rm "$IMAGE" || true
                '''
            }
        }
    }

    post {
        always {
            junit allowEmptyResults: true, testResults: 'TEST-*.xml'
            archiveArtifacts artifacts: 'coverage.xml', allowEmptyArchive: true
            publishHTML(target: [
                allowMissing: true,
                alwaysLinkToLastBuild: true,
                keepAll: true,
                reportDir: 'htmlcov',
                reportFiles: 'index.html',
                reportName: 'Coverage'
            ])
            sh 'rm -f TEST-*.xml'
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
            echo '构建未成功：请检查「代码检查」「单元测试与覆盖率」「Docker 构建」阶段日志。'
        }
    }
}
