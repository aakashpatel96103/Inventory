# Inventory Management System – End-to-End CI/CD

Version: v1.0.0

An Inventory Management System for managing products, stock and suppliers with an end-to-end DevOps pipeline.

## Application

- FastAPI REST API
- Products CRUD
- Suppliers CRUD
- Stock management
- Health endpoint: `/health`
- Metrics endpoint: `/metrics`
- Swagger: `/docs`
- Application port: `2001`

## DevOps Requirements

1. Git workflow: Git repository with status, branching and merge workflow.
2. Build automation: Jenkins installs Python dependencies and builds the application.
3. Automated testing: Pytest tests for health, products, suppliers, stock and metrics.
4. CI/CD: Jenkins pipeline automates test, build, scan, registry push and Kubernetes deployment.
5. Docker images: versioned image `inventory-service:v1.0.0`.
6. Container registry: local Docker Registry at `localhost:2000`.
7. Kubernetes: namespace, deployment and ClusterIP service.
8. ConfigMap: non-sensitive application settings (`APP_NAME`, `APP_VERSION`, `LOG_LEVEL`).
9. Secret: sensitive application key (`SECRET_KEY`).
10. Monitoring: Prometheus scrapes `/metrics`.
11. Logging: Python application logs and Kubernetes pod logs are checked by Jenkins.
12. Security scanning: Trivy scans the Docker image for HIGH and CRITICAL vulnerabilities.

## URLs

- Prometheus: http://localhost:1000
- Swagger: http://localhost:2001/docs
- Health: http://localhost:2001/health
- Metrics: http://localhost:2001/metrics
- Grafana: http://localhost:2002
- Registry: http://localhost:2000/v2/

## Kubernetes

Namespace: `inventory-system`

Application service: `inventory-service`

Monitoring namespace: `monitoring`

## CI/CD Flow

Git Workflow → Build → Test → Docker Build → Trivy Scan → Container Registry → ConfigMap/Secret → Kubernetes Deployment → Health/Logs → Monitoring → Services

## Rollback

The Jenkins deployment stage uses `kubectl rollout undo` if the Kubernetes deployment rollout fails. Kubernetes keeps five previous revisions using `revisionHistoryLimit: 5`.

## Git Workflow

Use feature branches for changes, run tests before merge, merge approved changes into the main branch, and let Jenkins build the resulting commit.
