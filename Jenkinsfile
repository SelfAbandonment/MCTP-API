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
        GITHUB_ACCOUNT = 'SelfAbandonment'
        GITHUB_REPO = 'MCTP-API'
        GITHUB_CREDENTIALS = 'github-MCTP'
        STATUS_CONTEXT = 'jenkins/mctp-api'
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
        always {
            script {
                notifyGitHub(currentBuild.currentResult)
            }
        }
        unsuccessful {
            echo '构建未成功：请检查「代码检查」「单元测试」「Docker 构建」阶段日志。'
        }
    }
}

/**
 * 把构建结果回写到 GitHub commit status，让 PR 能 require 这个检查。
 * 插件缺失或凭证不对时只打日志，不影响流水线结果。
 */
def notifyGitHub(String result) {
    if (!env.GIT_COMMIT) {
        echo '没有 GIT_COMMIT（可能不是 SCM 触发），跳过 GitHub 状态回写'
        return
    }
    def state = result == 'SUCCESS' ? 'SUCCESS' : (result == 'ABORTED' ? 'ERROR' : 'FAILURE')
    try {
        githubNotify account: env.GITHUB_ACCOUNT,
            credentialsId: env.GITHUB_CREDENTIALS,
            repo: env.GITHUB_REPO,
            sha: env.GIT_COMMIT,
            context: env.STATUS_CONTEXT,
            description: "Jenkins #${env.BUILD_NUMBER} ${result}",
            status: state
    } catch (Exception e) {
        echo "GitHub 状态回写失败（忽略）：${e.message}"
    }
}
