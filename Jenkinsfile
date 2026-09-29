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
                bat '''
                    python -m pip install -q -r inventory-service/requirements.txt
                    set PYTHONPATH=inventory-service&& python -m pytest inventory-service/tests -v
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                bat 'docker build -t %IMAGE% -t %REGISTRY_IMAGE% inventory-service'
            }
        }

        stage('Security Scan - Trivy') {
            steps {
                bat 'trivy image --severity HIGH,CRITICAL --exit-code 1 %IMAGE%'
            }
        }

        stage('Container Registry') {
            steps {
                bat '''
                    docker inspect inventory-registry >NUL 2>&1 || docker run -d -p 2000:5000 --restart unless-stopped --name inventory-registry registry:2
                    docker push %REGISTRY_IMAGE%
                '''
            }
        }

        stage('Load Image to Kubernetes') {
            steps {
                bat '''
                    docker save -o k8s.tar %IMAGE%
                    docker cp k8s.tar desktop-control-plane:/k8s.tar
                    docker exec desktop-control-plane ctr -n k8s.io images import /k8s.tar
                    docker exec desktop-control-plane rm -f /k8s.tar
                    del /f /q k8s.tar
                '''
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                script {
                    try {
                        bat '''
                            kubectl apply -f kubernetes -R
                            kubectl rollout status deployment/%APP% -n %NS% --timeout=120s
                            kubectl get pods -n %NS%
                            kubectl logs deployment/%APP% -n %NS% --tail=20
                        '''
                    } catch (Exception e) {
                        bat 'kubectl rollout undo deployment/%APP% -n %NS%'
                        throw e
                    }
                }
            }
        }

        stage('Start Services') {
            steps {
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
