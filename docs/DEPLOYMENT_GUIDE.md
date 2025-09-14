# 🚀 Deployment Guide

## Overview

This guide covers deployment strategies for the Delox delivery management system, from local development to production environments.

## 🏗️ Deployment Architecture

```mermaid
graph TB
    subgraph "Development Environment"
        DEV_DOCKER[Docker Compose]
        DEV_LOCAL[Local Development]
    end
    
    subgraph "Staging Environment"
        STAGE_K8S[Kubernetes Cluster]
        STAGE_DB[Managed Database]
        STAGE_CACHE[Managed Cache]
    end
    
    subgraph "Production Environment"
        PROD_K8S[Kubernetes Cluster]
        PROD_DB[Managed Database]
        PROD_CACHE[Managed Cache]
        PROD_CDN[CDN]
        PROD_LB[Load Balancer]
    end
    
    DEV_DOCKER --> STAGE_K8S
    STAGE_K8S --> PROD_K8S
```

## 🐳 Docker Compose (Development)

### Quick Start
```bash
# Clone repository
git clone <repository-url>
cd delox-delivery-system

# Set up environment
cp .env.example .env
# Edit .env with your configuration

# Install frontend dependencies
make install-frontend

# Start all services
make up

# Initialize database
make init-db

# Access the application
# Frontend: http://localhost:3000
# API: http://localhost:8080
# Traefik Dashboard: http://localhost:8081
```

### Environment Configuration
```bash
# .env file for development
DATABASE_URL=postgresql://delox_user:delox_password@postgres:5432/delox
REDIS_URL=redis://redis:6379
RABBITMQ_URL=amqp://delox:delox_password@rabbitmq:5672/

# Frontend
REACT_APP_API_URL=http://localhost:8080/api/v1
REACT_APP_ENVIRONMENT=development

# External APIs
GOOGLE_MAPS_API_KEY=your-google-maps-api-key
TWILIO_ACCOUNT_SID=your-twilio-account-sid
TWILIO_AUTH_TOKEN=your-twilio-auth-token
FCM_SERVER_KEY=your-fcm-server-key
```

### Service Health Checks
```bash
# Check all services
docker-compose ps

# Check specific service logs
make logs-auth
make logs-order
make logs-frontend

# Health check endpoints
curl http://localhost:8001/health  # Auth service
curl http://localhost:8002/health  # User service
curl http://localhost:8003/health  # Order service
```

## ☸️ Kubernetes Deployment

### Prerequisites
```bash
# Required tools
kubectl version --client
helm version
docker version

# Cluster access
kubectl cluster-info
kubectl get nodes
```

### Namespace Setup
```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: delox
  labels:
    name: delox
---
apiVersion: v1
kind: Namespace
metadata:
  name: delox-staging
  labels:
    name: delox-staging
```

### ConfigMaps and Secrets
```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: delox-config
  namespace: delox
data:
  ENVIRONMENT: "production"
  LOG_LEVEL: "info"
  CORS_ORIGINS: "https://app.delox.com"
  RATE_LIMIT_PER_MINUTE: "60"
---
apiVersion: v1
kind: Secret
metadata:
  name: delox-secrets
  namespace: delox
type: Opaque
stringData:
  DATABASE_URL: "postgresql://user:password@postgres:5432/delox"
  JWT_SECRET_KEY: "your-super-secret-jwt-key"
  GOOGLE_MAPS_API_KEY: "your-google-maps-api-key"
  TWILIO_AUTH_TOKEN: "your-twilio-auth-token"
  FCM_SERVER_KEY: "your-fcm-server-key"
```

### Database Deployment
```yaml
# k8s/postgres.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: delox
spec:
  serviceName: postgres
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15
        env:
        - name: POSTGRES_DB
          value: delox
        - name: POSTGRES_USER
          value: delox_user
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: delox-secrets
              key: POSTGRES_PASSWORD
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
  - metadata:
      name: postgres-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 20Gi
---
apiVersion: v1
kind: Service
metadata:
  name: postgres
  namespace: delox
spec:
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
```

### Microservice Deployment
```yaml
# k8s/auth-service.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: auth-service
  namespace: delox
spec:
  replicas: 3
  selector:
    matchLabels:
      app: auth-service
  template:
    metadata:
      labels:
        app: auth-service
    spec:
      containers:
      - name: auth-service
        image: delox/auth-service:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: delox-secrets
              key: DATABASE_URL
        - name: JWT_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: delox-secrets
              key: JWT_SECRET_KEY
        envFrom:
        - configMapRef:
            name: delox-config
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: auth-service
  namespace: delox
spec:
  selector:
    app: auth-service
  ports:
  - port: 8000
    targetPort: 8000
```

### Frontend Deployment
```yaml
# k8s/frontend.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: admin-dashboard
  namespace: delox
spec:
  replicas: 2
  selector:
    matchLabels:
      app: admin-dashboard
  template:
    metadata:
      labels:
        app: admin-dashboard
    spec:
      containers:
      - name: admin-dashboard
        image: delox/admin-dashboard:latest
        ports:
        - containerPort: 80
        env:
        - name: REACT_APP_API_URL
          value: "https://api.delox.com/api/v1"
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
---
apiVersion: v1
kind: Service
metadata:
  name: admin-dashboard
  namespace: delox
spec:
  selector:
    app: admin-dashboard
  ports:
  - port: 80
    targetPort: 80
```

### Ingress Configuration
```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: delox-ingress
  namespace: delox
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/rate-limit: "100"
spec:
  tls:
  - hosts:
    - app.delox.com
    - api.delox.com
    secretName: delox-tls
  rules:
  - host: app.delox.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: admin-dashboard
            port:
              number: 80
  - host: api.delox.com
    http:
      paths:
      - path: /api/v1/auth
        pathType: Prefix
        backend:
          service:
            name: auth-service
            port:
              number: 8000
      - path: /api/v1/users
        pathType: Prefix
        backend:
          service:
            name: user-service
            port:
              number: 8000
      - path: /api/v1/orders
        pathType: Prefix
        backend:
          service:
            name: order-service
            port:
              number: 8000
```

### Horizontal Pod Autoscaler
```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: auth-service-hpa
  namespace: delox
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: auth-service
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

## 🌩️ Cloud Provider Deployments

### AWS EKS
```bash
# Create EKS cluster
eksctl create cluster \
  --name delox-cluster \
  --region us-west-2 \
  --nodegroup-name delox-nodes \
  --node-type t3.medium \
  --nodes 3 \
  --nodes-min 1 \
  --nodes-max 10 \
  --managed

# Configure kubectl
aws eks update-kubeconfig --region us-west-2 --name delox-cluster

# Install AWS Load Balancer Controller
kubectl apply -k "github.com/aws/eks-charts/stable/aws-load-balancer-controller//crds?ref=master"
helm repo add eks https://aws.github.io/eks-charts
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=delox-cluster
```

### Google GKE
```bash
# Create GKE cluster
gcloud container clusters create delox-cluster \
  --zone us-central1-a \
  --num-nodes 3 \
  --enable-autoscaling \
  --min-nodes 1 \
  --max-nodes 10 \
  --machine-type e2-medium

# Get credentials
gcloud container clusters get-credentials delox-cluster --zone us-central1-a

# Install NGINX Ingress Controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/cloud/deploy.yaml
```

### Azure AKS
```bash
# Create resource group
az group create --name delox-rg --location eastus

# Create AKS cluster
az aks create \
  --resource-group delox-rg \
  --name delox-cluster \
  --node-count 3 \
  --enable-addons monitoring \
  --generate-ssh-keys

# Get credentials
az aks get-credentials --resource-group delox-rg --name delox-cluster
```

## 🔄 CI/CD Pipeline

### GitHub Actions
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Run Tests
      run: |
        docker-compose -f docker-compose.test.yml up --abort-on-container-exit
        docker-compose -f docker-compose.test.yml down

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Build and Push Images
      env:
        DOCKER_REGISTRY: ${{ secrets.DOCKER_REGISTRY }}
        DOCKER_USERNAME: ${{ secrets.DOCKER_USERNAME }}
        DOCKER_PASSWORD: ${{ secrets.DOCKER_PASSWORD }}
      run: |
        echo $DOCKER_PASSWORD | docker login $DOCKER_REGISTRY -u $DOCKER_USERNAME --password-stdin
        
        # Build and push all services
        docker build -t $DOCKER_REGISTRY/delox/auth-service:$GITHUB_SHA ./services/auth-service
        docker push $DOCKER_REGISTRY/delox/auth-service:$GITHUB_SHA
        
        docker build -t $DOCKER_REGISTRY/delox/admin-dashboard:$GITHUB_SHA ./frontend/admin-dashboard
        docker push $DOCKER_REGISTRY/delox/admin-dashboard:$GITHUB_SHA

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to Kubernetes
      env:
        KUBE_CONFIG: ${{ secrets.KUBE_CONFIG }}
      run: |
        echo "$KUBE_CONFIG" | base64 -d > kubeconfig
        export KUBECONFIG=kubeconfig
        
        # Update image tags
        kubectl set image deployment/auth-service auth-service=$DOCKER_REGISTRY/delox/auth-service:$GITHUB_SHA -n delox
        kubectl set image deployment/admin-dashboard admin-dashboard=$DOCKER_REGISTRY/delox/admin-dashboard:$GITHUB_SHA -n delox
        
        # Wait for rollout
        kubectl rollout status deployment/auth-service -n delox
        kubectl rollout status deployment/admin-dashboard -n delox
```

## 📊 Monitoring and Observability

### Prometheus and Grafana
```yaml
# k8s/monitoring.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: delox
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
    scrape_configs:
    - job_name: 'delox-services'
      kubernetes_sd_configs:
      - role: pod
        namespaces:
          names:
          - delox
      relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prometheus
  namespace: delox
spec:
  replicas: 1
  selector:
    matchLabels:
      app: prometheus
  template:
    metadata:
      labels:
        app: prometheus
    spec:
      containers:
      - name: prometheus
        image: prom/prometheus:latest
        ports:
        - containerPort: 9090
        volumeMounts:
        - name: config
          mountPath: /etc/prometheus
      volumes:
      - name: config
        configMap:
          name: prometheus-config
```

### Health Checks and Readiness Probes
```python
# Add to each service's main.py
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/health")
async def health_check():
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "service": "auth-service",
            "version": "1.0.0",
            "timestamp": datetime.utcnow().isoformat()
        }
    )

@app.get("/ready")
async def readiness_check():
    # Check database connection, external dependencies
    try:
        # Database health check
        await database.execute("SELECT 1")
        return JSONResponse(
            status_code=200,
            content={"status": "ready"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "not ready", "error": str(e)}
        )
```

## 🔒 Security Considerations

### Network Policies
```yaml
# k8s/network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: delox-network-policy
  namespace: delox
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
  - from:
    - podSelector: {}
  egress:
  - to:
    - podSelector: {}
  - to: []
    ports:
    - protocol: TCP
      port: 53
    - protocol: UDP
      port: 53
```

### Pod Security Standards
```yaml
# k8s/pod-security.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: delox
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

## 🚀 Production Checklist

### Pre-deployment
- [ ] Environment variables configured
- [ ] Secrets properly managed
- [ ] Database migrations tested
- [ ] SSL certificates configured
- [ ] Monitoring and alerting set up
- [ ] Backup strategy implemented
- [ ] Load testing completed
- [ ] Security scanning passed

### Post-deployment
- [ ] Health checks passing
- [ ] Monitoring dashboards working
- [ ] Log aggregation functioning
- [ ] Backup verification
- [ ] Performance metrics baseline
- [ ] Security monitoring active
- [ ] Documentation updated
- [ ] Team training completed

This deployment guide provides comprehensive instructions for deploying Delox across different environments and platforms.
