pipeline {
    agent any

    options {
        timestamps()
        timeout(time: 20, unit: 'MINUTES')
        disableConcurrentBuilds(abortPrevious: true)
        buildDiscarder(logRotator(numToKeepStr: '20', artifactNumToKeepStr: '10'))
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
                    uv run ruff check .
                    uv run ruff format --check .
                '''
            }
        }

        stage('单元测试') {
            steps {
                sh '''
                    set -e
                    export PATH="$HOME/.local/bin:$PATH"
                    uv run python manage.py check
                    uv run python manage.py test --verbosity=2
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
        unsuccessful {
            echo '构建未成功：请检查「代码检查」「单元测试」「Docker 构建」阶段日志。'
        }
    }
}
