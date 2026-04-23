# 🚀 Deployment Guide — Customer Success FTE

> **Purpose:** Step-by-step instructions for deploying the Digital FTE system.
> **Audience:** DevOps engineers, developers

---

## 📋 Prerequisites

| Requirement | Version | Notes |
|------------|---------|-------|
| **Docker** | 24+ | For local development |
| **Docker Compose** | 2.0+ | Included with Docker Desktop |
| **Python** | 3.12+ | For direct deployment |
| **Node.js** | 18+ | For frontend |
| **kubectl** | 1.28+ | For Kubernetes deployment |
| **Helm** | 3.0+ | Optional, for package management |

---

## 🖥️ Option 1: Local Development (Docker Compose)

### Step 1: Clone Repository

```bash
git clone <repository-url>
cd "The CRM Digital FTE Factory Hackathon 5"
```

### Step 2: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit with your credentials
nano .env  # or your preferred editor
```

Minimum required for local testing:
```env
OPENAI_API_KEY=sk-your-key-here
POSTGRES_PASSWORD=fte_password
```

### Step 3: Start Services

```bash
docker compose up -d
```

This starts:
- ✅ PostgreSQL (port 5432) — with schema auto-loaded
- ✅ Zookeeper (port 2181) — Kafka dependency
- ✅ Kafka (port 9092) — Event streaming
- ✅ FastAPI API (port 8000) — Backend service
- ✅ Message Processor Worker — Background agent

### Step 4: Start Frontend

```bash
cd web-form
npm install
npm run dev
```

### Step 5: Verify

```bash
# Check health
curl http://localhost:8000/health

# Check API docs
open http://localhost:8000/docs

# Check frontend
open http://localhost:3000
```

### Step 6: Test End-to-End

```bash
# Submit a support request
curl -X POST http://localhost:8000/support/submit \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "subject": "Password Reset",
    "category": "technical",
    "message": "How do I reset my password?"
  }'

# Check ticket status
curl http://localhost:8000/support/ticket/{ticket_id}
```

### Stop Services

```bash
docker compose down

# With data cleanup
docker compose down -v
```

---

## ☸️ Option 2: Kubernetes Production Deployment

### Step 1: Prepare Cluster

```bash
# Verify cluster access
kubectl cluster-info

# Create namespace
kubectl apply -f k8s/namespace.yaml
```

### Step 2: Configure Secrets

```bash
# Edit secrets.yaml with actual values
# Replace ${VARIABLE} placeholders with real credentials

# Apply secrets
kubectl apply -f k8s/secrets.yaml -n customer-success-fte

# Verify
kubectl get secrets -n customer-success-fte
```

### Step 3: Apply Configuration

```bash
kubectl apply -f k8s/configmap.yaml -n customer-success-fte
```

### Step 4: Deploy Infrastructure

```bash
# PostgreSQL (if not using managed database)
kubectl apply -f k8s/postgres.yaml -n customer-success-fte

# Kafka (if not using managed Kafka)
kubectl apply -f k8s/kafka.yaml -n customer-success-fte
```

### Step 5: Deploy Application

```bash
# Apply all manifests
kubectl apply -f k8s/deployment-api.yaml -n customer-success-fte
kubectl apply -f k8s/deployment-worker.yaml -n customer-success-fte
kubectl apply -f k8s/service.yaml -n customer-success-fte
kubectl apply -f k8s/ingress.yaml -n customer-success-fte
kubectl apply -f k8s/hpa.yaml -n customer-success-fte
```

### Step 6: Verify Deployment

```bash
# Check pods
kubectl get pods -n customer-success-fte

# Check services
kubectl get svc -n customer-success-fte

# Check ingress
kubectl get ingress -n customer-success-fte

# Check HPA
kubectl get hpa -n customer-success-fte

# View logs
kubectl logs -n customer-success-fte -l app=customer-success-fte -f
```

### Step 7: Initialize Database

```bash
# Run schema migration
kubectl exec -it -n customer-success-fte \
  $(kubectl get pod -n customer-success-fte -l component=postgres -o jsonpath='{.items[0].metadata.name}') \
  -- psql -U fte_user -d fte_db -f /docker-entrypoint-initdb.d/01-schema.sql
```

### Step 8: Configure DNS

```bash
# Point your domain to the ingress IP
# Get external IP
kubectl get ingress -n customer-success-fte

# Add DNS A record: support-api.yourdomain.com → EXTERNAL-IP
```

### Step 9: SSL Certificate (cert-manager)

```bash
# cert-manager should be installed in the cluster
# The ingress annotation cert-manager.io/cluster-issuer: letsencrypt-prod
# will automatically provision TLS certificates

# Check certificate status
kubectl get certificate -n customer-success-fte
```

---

## 🐳 Option 3: Docker Image Build & Push

### Build Image

```bash
docker build -t your-registry/customer-success-fte:v2.0.0 .
```

### Test Locally

```bash
docker run -d \
  --name fte-test \
  -p 8000:8000 \
  -e OPENAI_API_KEY=your-key \
  -e POSTGRES_HOST=host.docker.internal \
  -e POSTGRES_PASSWORD=fte_password \
  your-registry/customer-success-fte:v2.0.0
```

### Push to Registry

```bash
docker push your-registry/customer-success-fte:v2.0.0
```

### Update Kubernetes

```bash
kubectl set image deployment/fte-api \
  fte-api=your-registry/customer-success-fte:v2.0.0 \
  -n customer-success-fte

kubectl set image deployment/fte-message-processor \
  message-processor=your-registry/customer-success-fte:v2.0.0 \
  -n customer-success-fte
```

---

## 🌐 Option 4: Cloud Provider Deployment

### AWS EKS

```bash
# Create EKS cluster
eksctl create cluster --name fte-cluster --region us-east-1 --nodes 3

# Deploy
kubectl apply -f k8s/

# Use RDS for PostgreSQL
aws rds create-db-instance \
  --db-instance-identifier fte-db \
  --engine postgres \
  --db-instance-class db.t3.micro \
  --allocated-storage 20
```

### Google Cloud GKE

```bash
# Create GKE cluster
gcloud container clusters create fte-cluster --zone us-central1-a --num-nodes 3

# Deploy
kubectl apply -f k8s/

# Use Cloud SQL for PostgreSQL
gcloud sql instances create fte-db --database-version=POSTGRES_16 --tier=db-f1-micro
```

### Azure AKS

```bash
# Create AKS cluster
az aks create --resource-group fte-rg --name fte-cluster --node-count 3

# Deploy
kubectl apply -f k8s/

# Use Azure Database for PostgreSQL
az postgres flexible-server create --name fte-db --resource-group fte-rg
```

---

## 🔧 Post-Deployment Checklist

- [ ] Health check returns 200: `curl https://support-api.yourdomain.com/health`
- [ ] Frontend loads: `open https://support.yourdomain.com`
- [ ] API docs accessible: `open https://support-api.yourdomain.com/docs`
- [ ] Database schema applied
- [ ] Kafka topics created (auto-created on first message)
- [ ] SSL certificate valid
- [ ] DNS records configured
- [ ] Monitoring alerts configured
- [ ] Backup schedule set up
- [ ] Log aggregation configured
- [ ] Rate limiting configured (if needed)

---

## 🔄 Rolling Updates

```bash
# Update image
kubectl set image deployment/fte-api \
  fte-api=your-registry/customer-success-fte:v2.1.0 \
  -n customer-success-fte

# Monitor rollout
kubectl rollout status deployment/fte-api -n customer-success-fte

# Rollback if needed
kubectl rollout undo deployment/fte-api -n customer-success-fte
```

---

## 🚨 Troubleshooting

### Pod won't start

```bash
# Check events
kubectl describe pod <pod-name> -n customer-success-fte

# Check logs
kubectl logs <pod-name> -n customer-success-fte

# Common issues:
# - Image pull error: Check registry credentials
# - CrashLoopBackOff: Check application logs
# - Pending: Check cluster resources
```

### Database connection fails

```bash
# Test connectivity
kubectl run -it --rm debug --image=postgres:16 --restart=Never -- \
  psql -h postgres.customer-success-fte.svc.cluster.local -U fte_user -d fte_db

# Check service
kubectl get svc postgres -n customer-success-fte
```

### Kafka connection fails

```bash
# Test connectivity
kubectl run -it --rm debug --image=confluentinc/cp-kafka:7.5.0 --restart=Never -- \
  kafka-broker-api-versions --bootstrap-server kafka.kafka.svc.cluster.local:9092
```

---

*Last updated: April 7, 2026*
