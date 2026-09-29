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
        stage('Git Workflow') {
            steps {
                bat 'git status --short'
            }
        }

        stage('Build Automation') {
            steps {
                bat 'python -m pip install -r inventory-service/requirements.txt'
            }
        }

        stage('Automated Testing') {
            steps {
                bat 'python -m pytest inventory-service/tests -v'
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
                    docker rm -f inventory-registry 2>NUL || exit /b 0
                    docker run -d -p 5000:5000 --restart unless-stopped --name inventory-registry registry:2
                    timeout /t 5 /nobreak >NUL
                    docker push %REGISTRY_IMAGE%
                '''
            }
        }

        stage('Prepare Kubernetes') {
            steps {
                bat '''
                    kubectl apply -f kubernetes/namespace.yaml
                    kubectl apply -f kubernetes/monitoring/namespace.yaml
                    kubectl apply -f kubernetes/inventory-service-configmap.yaml
                    kubectl apply -f kubernetes/inventory-service-secret.yaml
                    kubectl apply -f kubernetes/monitoring/prometheus.yaml
                    kubectl apply -f kubernetes/monitoring/grafana.yaml
                '''
            }
        }

        stage('Load Image to Kubernetes') {
            steps {
                bat '''
                    docker save -o k8s.tar %IMAGE%
                    docker cp k8s.tar desktop-control-plane:/k8s.tar
                    docker exec desktop-control-plane ctr -n k8s.io images import /k8s.tar
                    del /f /q k8s.tar
                '''
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                script {
                    try {
                        bat '''
                            kubectl apply -f kubernetes/inventory-service-deployment.yaml
                            kubectl apply -f kubernetes/inventory-service.yaml
                            kubectl rollout status deployment/%APP% -n %NS% --timeout=120s
                        '''
                    } catch (Exception e) {
                        bat 'kubectl rollout undo deployment/%APP% -n %NS%'
                        throw e
                    }
                }
            }
        }

        stage('Health & Metrics Validation') {
            steps {
                bat '''
                    kubectl rollout status deployment/%APP% -n %NS% --timeout=120s
                    kubectl get pods -n %NS%
                    kubectl logs deployment/%APP% -n %NS% --tail=20
                '''
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
