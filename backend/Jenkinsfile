pipeline {
    agent any

    environment {
        DOCKERHUB_USER   = "devsharvari"
        GITHUB_USER      = "Sharvari-1315"
        BACKEND_IMAGE    = "${DOCKERHUB_USER}/message-board-backend"
        FRONTEND_IMAGE   = "${DOCKERHUB_USER}/message-board-frontend"
        IMAGE_TAG        = "${BUILD_NUMBER}"
        GITOPS_REPO      = "github.com/${GITHUB_USER}/message-board-devsecops.git"
        SONAR_PROJECT    = "message-board"
    }

    stages {

        stage('Checkout') {
            steps {
                git branch: 'main',
                    url: "https://github.com/${GITHUB_USER}/message-board-devsecops.git"
                echo "✅ Code checked out"
            }
        }

        stage('SAST - SonarQube Scan') {
            steps {
                withSonarQubeEnv('SonarQube') {
                    sh """
                        sonar-scanner \
                          -Dsonar.projectKey=${SONAR_PROJECT} \
                          -Dsonar.sources=./backend \
                          -Dsonar.host.url=http://localhost:9000
                    """
                }
                echo "✅ SonarQube scan done"
            }
        }

        stage('Quality Gate') {
            steps {
                timeout(time: 2, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
                echo "✅ Quality Gate passed"
            }
        }

        stage('Build Docker Images') {
            parallel {
                stage('Build Backend') {
                    steps {
                        sh "docker build -t ${BACKEND_IMAGE}:${IMAGE_TAG} ./backend"
                        echo "✅ Backend image built"
                    }
                }
                stage('Build Frontend') {
                    steps {
                        sh "docker build -t ${FRONTEND_IMAGE}:${IMAGE_TAG} ./frontend"
                        echo "✅ Frontend image built"
                    }
                }
            }
        }

        stage('Trivy Security Scan') {
            parallel {
                stage('Scan Backend') {
                    steps {
                        sh """
                            trivy image \
                              --severity HIGH,CRITICAL \
                              --format table \
                              --output trivy-backend.txt \
                              --exit-code 0 \
                              ${BACKEND_IMAGE}:${IMAGE_TAG}
                        """
                        // Change --exit-code 0 to --exit-code 1 to FAIL on HIGH/CRITICAL
                        echo "✅ Backend scan done"
                    }
                }
                stage('Scan Frontend') {
                    steps {
                        sh """
                            trivy image \
                              --severity HIGH,CRITICAL \
                              --format table \
                              --output trivy-frontend.txt \
                              --exit-code 0 \
                              ${FRONTEND_IMAGE}:${IMAGE_TAG}
                        """
                        echo "✅ Frontend scan done"
                    }
                }
            }
            post {
                always {
                    archiveArtifacts artifacts: 'trivy-*.txt', allowEmptyArchive: true
                }
            }
        }

        stage('Push to Docker Hub') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub-credentials',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    sh """
                        echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin
                        docker push ${BACKEND_IMAGE}:${IMAGE_TAG}
                        docker push ${FRONTEND_IMAGE}:${IMAGE_TAG}
                    """
                }
                echo "✅ Images pushed to Docker Hub"
            }
        }

        stage('Update Image Tags in Repo') {
            // This updates the image tag in k8s yaml files
            // ArgoCD watches this repo and auto-deploys the new tag
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'github-credentials',
                    usernameVariable: 'GIT_USER',
                    passwordVariable: 'GIT_PASS'
                )]) {
                    sh """
                        git config user.email "jenkins@ci.com"
                        git config user.name "Jenkins CI"

                        # Update backend image tag
                        sed -i 's|${BACKEND_IMAGE}:.*|${BACKEND_IMAGE}:${IMAGE_TAG}|g' k8s/backend/backend.yaml

                        # Update frontend image tag
                        sed -i 's|${FRONTEND_IMAGE}:.*|${FRONTEND_IMAGE}:${IMAGE_TAG}|g' k8s/frontend/frontend.yaml

                        git add k8s/backend/backend.yaml k8s/frontend/frontend.yaml
                        git commit -m "ci: update image tags to build-${IMAGE_TAG} [skip ci]"
                        git push https://${GIT_USER}:${GIT_PASS}@${GITOPS_REPO} main
                    """
                }
                echo "✅ Image tags updated — ArgoCD will now sync to Minikube"
            }
        }
    }

    post {
        success {
            echo "✅ Pipeline complete! ArgoCD is deploying build-${IMAGE_TAG} to Minikube."
        }
        failure {
            echo "❌ Pipeline failed. Check the stage logs above."
        }
        always {
            sh "docker rmi ${BACKEND_IMAGE}:${IMAGE_TAG} ${FRONTEND_IMAGE}:${IMAGE_TAG} || true"
            sh "docker logout || true"
            cleanWs()
        }
    }
}
