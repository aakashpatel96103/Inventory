pipeline {
    agent any

    environment {
        APP = 'inventory-service'
        NS = 'inventory-system'
        MON = 'monitoring'
        VERSION = 'v1.0.0'
        IMAGE = 'inventory-service:v1.0.0'
        REGISTRY_IMAGE = 'localhost:2000/inventory-service:v1.0.0'
    }

    stages {
        stage('Automated Testing') {
            steps {
                script {
                    if (isUnix()) {
                        sh '''
                            python3 -m pip install -q -r inventory-service/requirements.txt || pip install -q -r inventory-service/requirements.txt
                            PYTHONPATH=inventory-service python3 -m pytest inventory-service/tests -v || PYTHONPATH=inventory-service python -m pytest inventory-service/tests -v
                        '''
                    } else {
                        bat '''
                            python -m pip install -q -r inventory-service/requirements.txt
                            set PYTHONPATH=inventory-service&& python -m pytest inventory-service/tests -v
                        '''
                    }
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    if (isUnix()) {
                        sh 'docker build -t ${IMAGE} -t ${REGISTRY_IMAGE} inventory-service'
                    } else {
                        bat 'docker build -t %IMAGE% -t %REGISTRY_IMAGE% inventory-service'
                    }
                }
            }
        }

        stage('Security Scan - Trivy') {
            steps {
                script {
                    catchError(buildResult: 'SUCCESS', stageResult: 'UNSTABLE') {
                        def hasTrivy = false
                        try {
                            if (isUnix()) {
                                sh 'command -v trivy >/dev/null 2>&1'
                            } else {
                                bat 'where trivy >NUL 2>&1'
                            }
                            hasTrivy = true
                        } catch (Exception ignored) {
                            hasTrivy = false
                        }

                        if (hasTrivy) {
                            echo 'Running locally installed Trivy...'
                            if (isUnix()) {
                                sh 'trivy image --severity HIGH,CRITICAL --ignore-unfixed --exit-code 1 ${IMAGE}'
                            } else {
                                bat 'trivy image --severity HIGH,CRITICAL --ignore-unfixed --exit-code 1 %IMAGE%'
                            }
                        } else {
                            echo 'Trivy CLI not found; running Trivy via official Docker container...'
                            if (isUnix()) {
                                sh 'docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy:latest image --severity HIGH,CRITICAL --ignore-unfixed --exit-code 1 ${IMAGE}'
                            } else {
                                bat 'docker run --rm -v //var/run/docker.sock:/var/run/docker.sock aquasec/trivy:latest image --severity HIGH,CRITICAL --ignore-unfixed --exit-code 1 %IMAGE%'
                            }
                        }
                    }
                }
            }
        }

        stage('Container Registry') {
            steps {
                script {
                    if (isUnix()) {
                        sh '''
                            docker inspect inventory-registry >/dev/null 2>&1 || docker run -d -p 2000:5000 --restart unless-stopped --name inventory-registry registry:2
                            docker push ${REGISTRY_IMAGE}
                        '''
                    } else {
                        bat '''
                            docker inspect inventory-registry >NUL 2>&1 || docker run -d -p 2000:5000 --restart unless-stopped --name inventory-registry registry:2
                            docker push %REGISTRY_IMAGE%
                        '''
                    }
                }
            }
        }

        stage('Load Image to Kubernetes') {
            steps {
                script {
                    def k8sContext = ''
                    try {
                        k8sContext = isUnix() ?
                            sh(returnStdout: true, script: 'kubectl config current-context 2>/dev/null || true').trim() :
                            bat(returnStdout: true, script: '@kubectl config current-context 2>NUL || echo unknown').trim()
                    } catch (Exception e) {
                        k8sContext = 'unknown'
                    }

                    echo "Detected Kubernetes Context: ${k8sContext}"

                    if (k8sContext.toLowerCase().contains('minikube')) {
                        echo "Loading image into Minikube cluster..."
                        if (isUnix()) { sh 'minikube image load ${IMAGE}' }
                        else { bat 'minikube image load %IMAGE%' }
                    } else if (k8sContext.toLowerCase().contains('kind')) {
                        echo "Loading image into Kind cluster..."
                        if (isUnix()) { sh 'kind load docker-image ${IMAGE}' }
                        else { bat 'kind load docker-image %IMAGE%' }
                    } else {
                        def hasControlPlane = false
                        try {
                            if (isUnix()) {
                                sh 'docker inspect desktop-control-plane >/dev/null 2>&1'
                            } else {
                                bat 'docker inspect desktop-control-plane >NUL 2>&1'
                            }
                            hasControlPlane = true
                        } catch (Exception ignored) {
                            hasControlPlane = false
                        }

                        if (hasControlPlane) {
                            echo "Loading image into desktop-control-plane..."
                            if (isUnix()) {
                                sh '''
                                    docker save -o k8s.tar ${IMAGE}
                                    docker cp k8s.tar desktop-control-plane:/k8s.tar
                                    docker exec desktop-control-plane ctr -n k8s.io images import /k8s.tar
                                    docker exec desktop-control-plane rm -f /k8s.tar
                                    rm -f k8s.tar
                                '''
                            } else {
                                bat '''
                                    docker save -o k8s.tar %IMAGE%
                                    docker cp k8s.tar desktop-control-plane:/k8s.tar
                                    docker exec desktop-control-plane ctr -n k8s.io images import /k8s.tar
                                    docker exec desktop-control-plane rm -f /k8s.tar
                                    del /f /q k8s.tar
                                '''
                            }
                        } else {
                            echo "Using registry image ${REGISTRY_IMAGE} for Kubernetes."
                        }
                    }
                }
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                script {
                    try {
                        if (isUnix()) {
                            sh '''
                                kubectl apply -f kubernetes -R
                                kubectl rollout status deployment/${APP} -n ${NS} --timeout=120s
                                kubectl get pods -n ${NS}
                                kubectl logs deployment/${APP} -n ${NS} --tail=20
                            '''
                        } else {
                            bat '''
                                kubectl apply -f kubernetes -R
                                kubectl rollout status deployment/%APP% -n %NS% --timeout=120s
                                kubectl get pods -n %NS%
                                kubectl logs deployment/%APP% -n %NS% --tail=20
                            '''
                        }
                    } catch (Exception e) {
                        if (isUnix()) {
                            sh 'kubectl rollout undo deployment/${APP} -n ${NS}'
                        } else {
                            bat 'kubectl rollout undo deployment/%APP% -n %NS%'
                        }
                        throw e
                    }
                }
            }
        }

        stage('Start Services') {
            steps {
                script {
                    if (isUnix()) {
                        sh '''
                            export JENKINS_NODE_COOKIE=dontKillMe
                            fuser -k 1000/tcp 2001/tcp 2002/tcp 2>/dev/null || true
                            nohup kubectl port-forward service/prometheus 1000:1000 -n ${MON} >/dev/null 2>&1 &
                            nohup kubectl port-forward service/inventory-service 2001:2001 -n ${NS} >/dev/null 2>&1 &
                            nohup kubectl port-forward service/grafana 2002:2002 -n ${MON} >/dev/null 2>&1 &
                            exit 0
                        '''
                    } else {
                        bat '''
                            set JENKINS_NODE_COOKIE=dontKillMe
                            powershell -NoProfile -Command "Get-Process -Id (Get-NetTCPConnection -LocalPort 1000,2001,2002 -ErrorAction SilentlyContinue).OwningProcess -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue; exit 0"
                            start /B kubectl port-forward service/prometheus 1000:1000 -n %MON%
                            start /B kubectl port-forward service/inventory-service 2001:2001 -n %NS%
                            start /B kubectl port-forward service/grafana 2002:2002 -n %MON%
                            exit /b 0
                        '''
                    }
                }
            }
        }
    }

    post {
        success {
            echo '======================================================='
            echo 'INVENTORY CI/CD PIPELINE COMPLETED SUCCESSFULLY'
            echo 'Prometheus: http://localhost:1000'
            echo 'API Docs:   http://localhost:2001/docs'
            echo 'Grafana:    http://localhost:2002'
            echo 'Registry:   localhost:2000/inventory-service:v1.0.0'
            echo '======================================================='
        }
        failure {
            echo 'Pipeline failed. Kubernetes rollback is attempted when deployment rollout fails.'
        }
    }
}
