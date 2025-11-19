# MindScout Deployment Guide - Google Cloud Platform (GCP)

## Overview

This guide covers deploying MindScout to GCP using modern, scalable architecture.

## Architecture Options

### Option 1: **Cloud Run** (Recommended - Serverless, Auto-scaling)

```
┌─────────────────────────────────────────────────────────┐
│                     GCP Architecture                     │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Cloud Storage      Cloud Run           Cloud SQL       │
│  (Frontend) ──────> (Backend API) ────> (PostgreSQL)    │
│      │                   │                               │
│      │                   └──────────────> Cloud Tasks    │
│      │                                    (Scheduling)   │
│      │                                                    │
│      └──────> Cloud CDN                                  │
│                                                          │
│  Secret Manager: API keys, DB passwords                 │
│  Cloud Build: CI/CD automation                          │
│  Cloud Logging: Centralized logs                        │
└─────────────────────────────────────────────────────────┘
```

**Cost Estimate**: $10-30/month (with free tier)
**Best for**: Auto-scaling, pay-per-use, minimal ops

### Option 2: **GKE** (Kubernetes - Production Scale)

```
┌─────────────────────────────────────────────────────────┐
│                  GKE (Kubernetes)                        │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Load Balancer ──> Ingress Controller                   │
│                         │                                │
│                    ┌────┴────┐                          │
│                    │         │                          │
│              Frontend Pod  Backend Pods (3x)            │
│                              │                          │
│                         ┌────┴────┐                     │
│                         │         │                     │
│                    Cloud SQL   Redis (Memorystore)      │
│                                                          │
│  Worker Pods: Background tasks                          │
│  Horizontal Pod Autoscaler: Auto-scaling                │
└─────────────────────────────────────────────────────────┘
```

**Cost Estimate**: $100-300/month
**Best for**: High traffic, complex microservices

### Option 3: **Compute Engine VM** (Traditional VPS)

**Cost Estimate**: $15-50/month
**Best for**: Full control, learning

---

## 🚀 Recommended: Cloud Run Deployment

### Prerequisites

```bash
# Install Google Cloud SDK
# macOS
brew install google-cloud-sdk

# Linux
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Initialize gcloud
gcloud init

# Login
gcloud auth login

# Set project
gcloud config set project YOUR_PROJECT_ID
```

### Step 1: Project Setup

```bash
# Create new GCP project
export PROJECT_ID="mindscout-prod"
export REGION="us-central1"

gcloud projects create $PROJECT_ID
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  sqladmin.googleapis.com \
  secretmanager.googleapis.com \
  cloudtasks.googleapis.com \
  storage.googleapis.com \
  compute.googleapis.com
```

### Step 2: Setup Cloud SQL (PostgreSQL)

```bash
# Create Cloud SQL instance
gcloud sql instances create mindscout-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=$REGION \
  --storage-type=SSD \
  --storage-size=10GB \
  --backup \
  --maintenance-window-day=SUN \
  --maintenance-window-hour=3

# Set root password
gcloud sql users set-password postgres \
  --instance=mindscout-db \
  --password=$(openssl rand -base64 32)

# Create database
gcloud sql databases create mindscout \
  --instance=mindscout-db

# Create application user
gcloud sql users create mindscout_user \
  --instance=mindscout-db \
  --password=$(openssl rand -base64 32)

# Get connection name (save this!)
gcloud sql instances describe mindscout-db \
  --format='value(connectionName)'
# Output: PROJECT_ID:REGION:mindscout-db
```

### Step 3: Store Secrets

```bash
# Create secrets
echo -n "your-anthropic-api-key" | \
  gcloud secrets create anthropic-api-key \
  --data-file=-

echo -n "postgresql://mindscout_user:PASSWORD@/mindscout?host=/cloudsql/PROJECT_ID:REGION:mindscout-db" | \
  gcloud secrets create database-url \
  --data-file=-

# Generate secret key for sessions
echo -n "$(openssl rand -hex 32)" | \
  gcloud secrets create secret-key \
  --data-file=-
```

### Step 4: Prepare Application for Cloud Run

**Create `Dockerfile` in project root**:

```dockerfile
# Multi-stage build for smaller image
FROM python:3.10-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Final stage
FROM python:3.10-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local

# Copy application
COPY . .
RUN pip install -e .

# Make sure scripts are in PATH
ENV PATH=/root/.local/bin:$PATH

# Cloud Run expects port 8080
ENV PORT=8080

# Run migrations and start server
CMD python -c "from mindscout.database import init_db; init_db()" && \
    exec uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

**Create `requirements.txt`**:

```bash
cat > requirements.txt << 'EOF'
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.0.0
sqlalchemy>=2.0.0
psycopg2-binary>=2.9.0
anthropic>=0.40.0
feedparser>=6.0.10
requests>=2.31.0
numpy>=1.24.0
chromadb>=0.4.0
sentence-transformers>=2.2.0
google-cloud-secret-manager>=2.16.0
google-cloud-storage>=2.10.0
EOF
```

**Update `backend/main.py` for Cloud Run**:

```python
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import Cloud SQL connector if using Cloud SQL
from google.cloud.sql.connector import Connector

app = FastAPI(title="MindScout API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint for Cloud Run
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Include your routers
from backend.api import articles, profile, recommendations, search
app.include_router(articles.router, prefix="/api")
app.include_router(profile.router, prefix="/api")
app.include_router(recommendations.router, prefix="/api")
app.include_router(search.router, prefix="/api")
```

**Create `cloudbuild.yaml` for CI/CD**:

```yaml
steps:
  # Build the container image
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'build'
      - '-t'
      - 'gcr.io/$PROJECT_ID/mindscout-backend:$COMMIT_SHA'
      - '-t'
      - 'gcr.io/$PROJECT_ID/mindscout-backend:latest'
      - '.'

  # Push the image to Container Registry
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'push'
      - 'gcr.io/$PROJECT_ID/mindscout-backend:$COMMIT_SHA'

  # Deploy to Cloud Run
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'deploy'
      - 'mindscout-backend'
      - '--image'
      - 'gcr.io/$PROJECT_ID/mindscout-backend:$COMMIT_SHA'
      - '--region'
      - 'us-central1'
      - '--platform'
      - 'managed'
      - '--allow-unauthenticated'
      - '--set-env-vars'
      - 'PROJECT_ID=$PROJECT_ID'
      - '--set-secrets'
      - 'ANTHROPIC_API_KEY=anthropic-api-key:latest,DATABASE_URL=database-url:latest,SECRET_KEY=secret-key:latest'
      - '--add-cloudsql-instances'
      - '$PROJECT_ID:us-central1:mindscout-db'
      - '--max-instances'
      - '10'
      - '--memory'
      - '512Mi'
      - '--cpu'
      - '1'
      - '--timeout'
      - '300'

images:
  - 'gcr.io/$PROJECT_ID/mindscout-backend:$COMMIT_SHA'
  - 'gcr.io/$PROJECT_ID/mindscout-backend:latest'
```

### Step 5: Deploy Backend to Cloud Run

```bash
# Build and submit to Cloud Build
gcloud builds submit \
  --tag gcr.io/$PROJECT_ID/mindscout-backend

# Deploy to Cloud Run
gcloud run deploy mindscout-backend \
  --image gcr.io/$PROJECT_ID/mindscout-backend \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --set-secrets="ANTHROPIC_API_KEY=anthropic-api-key:latest,DATABASE_URL=database-url:latest,SECRET_KEY=secret-key:latest" \
  --add-cloudsql-instances=$PROJECT_ID:$REGION:mindscout-db \
  --max-instances=10 \
  --memory=512Mi \
  --cpu=1 \
  --timeout=300

# Get the service URL
gcloud run services describe mindscout-backend \
  --platform managed \
  --region $REGION \
  --format 'value(status.url)'
# Save this URL - you'll need it for the frontend!
```

### Step 6: Deploy Frontend to Cloud Storage + CDN

```bash
# Build frontend
cd frontend

# Update API URL
cat > .env.production << EOF
VITE_API_URL=https://YOUR-BACKEND-URL.run.app/api
EOF

# Build
npm install
npm run build

# Create bucket for static hosting
gsutil mb -l $REGION gs://$PROJECT_ID-frontend

# Upload files
gsutil -m cp -r dist/* gs://$PROJECT_ID-frontend/

# Make files public
gsutil -m acl ch -r -u AllUsers:R gs://$PROJECT_ID-frontend/*

# Set bucket as website
gsutil web set -m index.html -e index.html gs://$PROJECT_ID-frontend

# Setup Cloud CDN (optional but recommended)
gcloud compute backend-buckets create mindscout-frontend-backend \
  --gcs-bucket-name=$PROJECT_ID-frontend \
  --enable-cdn

# Create URL map
gcloud compute url-maps create mindscout-frontend-url-map \
  --default-backend-bucket=mindscout-frontend-backend

# Create HTTP proxy
gcloud compute target-http-proxies create mindscout-frontend-proxy \
  --url-map=mindscout-frontend-url-map

# Reserve static IP
gcloud compute addresses create mindscout-frontend-ip \
  --global

# Get the IP
gcloud compute addresses describe mindscout-frontend-ip \
  --global \
  --format="value(address)"

# Create forwarding rule
gcloud compute forwarding-rules create mindscout-frontend-rule \
  --global \
  --target-http-proxy=mindscout-frontend-proxy \
  --address=mindscout-frontend-ip \
  --ports=80
```

### Step 7: Setup Custom Domain (Optional)

```bash
# After setting up DNS A record to the IP above:

# Create SSL certificate
gcloud compute ssl-certificates create mindscout-cert \
  --domains=mindscout.yourdomain.com

# Create HTTPS proxy
gcloud compute target-https-proxies create mindscout-frontend-https-proxy \
  --url-map=mindscout-frontend-url-map \
  --ssl-certificates=mindscout-cert

# Create HTTPS forwarding rule
gcloud compute forwarding-rules create mindscout-frontend-https-rule \
  --global \
  --target-https-proxy=mindscout-frontend-https-proxy \
  --address=mindscout-frontend-ip \
  --ports=443

# Map custom domain to Cloud Run backend
gcloud run domain-mappings create \
  --service=mindscout-backend \
  --domain=api.yourdomain.com \
  --region=$REGION
```

### Step 8: Setup Scheduled Tasks (Background Fetching)

**Create task handler in `backend/tasks.py`**:

```python
from fastapi import APIRouter, Header, HTTPException
import hashlib
import hmac
import os

router = APIRouter()

@router.post("/tasks/fetch-papers")
async def fetch_papers_task(
    x_cloudtasks_taskname: str = Header(None),
    x_cloudtasks_queuename: str = Header(None)
):
    """Triggered by Cloud Tasks to fetch new papers."""
    # Verify it's from Cloud Tasks
    if not x_cloudtasks_taskname:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Your fetching logic here
    from mindscout.fetchers.arxiv import fetch_arxiv
    from mindscout.fetchers.semanticscholar import SemanticScholarFetcher

    # Fetch from arXiv
    arxiv_count = fetch_arxiv(categories=["cs.AI", "cs.LG", "cs.CV", "cs.CL"])

    # Fetch trending papers from Semantic Scholar
    fetcher = SemanticScholarFetcher()
    papers = fetcher.fetch(query="machine learning", limit=20, min_citations=50)
    ss_count = fetcher.save_to_db(papers)
    fetcher.close()

    return {
        "status": "success",
        "arxiv_papers": arxiv_count,
        "semanticscholar_papers": ss_count
    }
```

**Setup Cloud Scheduler**:

```bash
# Create Cloud Tasks queue
gcloud tasks queues create mindscout-tasks \
  --location=$REGION

# Create Cloud Scheduler job (daily at 9am)
gcloud scheduler jobs create http fetch-daily-papers \
  --location=$REGION \
  --schedule="0 9 * * *" \
  --uri="https://YOUR-BACKEND-URL.run.app/tasks/fetch-papers" \
  --http-method=POST \
  --oidc-service-account-email=YOUR-PROJECT-NUMBER-compute@developer.gserviceaccount.com \
  --oidc-token-audience="https://YOUR-BACKEND-URL.run.app"
```

### Step 9: Setup Monitoring & Logging

```bash
# Cloud Run automatically sends logs to Cloud Logging

# View logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=mindscout-backend" \
  --limit=50 \
  --format=json

# Create log-based metric for errors
gcloud logging metrics create backend_errors \
  --description="Count of backend errors" \
  --log-filter='resource.type="cloud_run_revision"
    resource.labels.service_name="mindscout-backend"
    severity>=ERROR'

# Create uptime check
gcloud monitoring uptime create mindscout-uptime \
  --resource-type=uptime-url \
  --display-name="MindScout Backend Health" \
  --url="https://YOUR-BACKEND-URL.run.app/health" \
  --check-interval=60s

# Setup alerting (optional)
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="Backend Down Alert" \
  --condition-display-name="Uptime check failed" \
  --condition-threshold-value=1 \
  --condition-threshold-duration=300s
```

### Step 10: CI/CD with Cloud Build Triggers

```bash
# Connect GitHub repository
gcloud beta builds triggers create github \
  --name=mindscout-backend-deploy \
  --repo-name=mindscout \
  --repo-owner=YOUR-GITHUB-USERNAME \
  --branch-pattern=^main$ \
  --build-config=cloudbuild.yaml

# Now every push to main automatically deploys!
```

---

## 🔧 Configuration Files

### Update `mindscout/config.py`

```python
import os
from google.cloud import secretmanager

def get_secret(secret_id: str) -> str:
    """Fetch secret from Secret Manager."""
    if os.getenv("GAE_ENV", "").startswith("standard"):
        # Running on GCP
        project_id = os.getenv("PROJECT_ID")
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    else:
        # Local development - use environment variables
        return os.getenv(secret_id.upper().replace("-", "_"), "")

# Database
DATABASE_URL = get_secret("database-url") or os.getenv("DATABASE_URL")

# API Keys
ANTHROPIC_API_KEY = get_secret("anthropic-api-key") or os.getenv("ANTHROPIC_API_KEY")

# Security
SECRET_KEY = get_secret("secret-key") or os.getenv("SECRET_KEY", "dev-secret-key")
```

### Update `backend/database.py` for Cloud SQL

```python
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from google.cloud.sql.connector import Connector

def get_db_engine():
    """Create database engine with Cloud SQL connector."""
    db_url = os.getenv("DATABASE_URL")

    if "cloudsql" in db_url:
        # Use Cloud SQL Python Connector
        connector = Connector()

        def getconn():
            return connector.connect(
                os.getenv("INSTANCE_CONNECTION_NAME"),
                "pg8000",
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                db=os.getenv("DB_NAME")
            )

        engine = create_engine(
            "postgresql+pg8000://",
            creator=getconn,
        )
    else:
        # Local development
        engine = create_engine(db_url)

    return engine

engine = get_db_engine()
Session = sessionmaker(bind=engine)
```

---

## 💰 Cost Breakdown (Monthly Estimates)

### Minimal Setup (< 1000 users):
- **Cloud Run**: $0-5 (2M requests free, then $0.40/M)
- **Cloud SQL** (db-f1-micro): $7
- **Cloud Storage**: $0.20
- **Cloud CDN**: $0-2
- **Secrets Manager**: $0.06
- **Cloud Build**: Free (120 min/day)
- **Total: ~$10-15/month**

### Medium Setup (1K-10K users):
- **Cloud Run**: $10-30
- **Cloud SQL** (db-g1-small): $25
- **Cloud Storage + CDN**: $5
- **Cloud Tasks**: $1
- **Cloud Logging**: $5
- **Total: ~$50-70/month**

### Production (10K+ users):
- **Cloud Run** (multi-region): $100-200
- **Cloud SQL** (HA, replicas): $150-300
- **Memorystore Redis**: $50
- **Cloud CDN**: $20-50
- **Cloud Armor** (DDoS): $10
- **Total: ~$400-600/month**

---

## 🎯 Quick Start Commands

```bash
# One-time setup
export PROJECT_ID="mindscout-prod"
export REGION="us-central1"

gcloud config set project $PROJECT_ID

# Deploy in 5 commands
gcloud sql instances create mindscout-db --database-version=POSTGRES_15 --tier=db-f1-micro --region=$REGION
gcloud sql databases create mindscout --instance=mindscout-db

gcloud builds submit --tag gcr.io/$PROJECT_ID/mindscout-backend
gcloud run deploy mindscout-backend --image gcr.io/$PROJECT_ID/mindscout-backend --region $REGION

cd frontend && npm run build && gsutil -m cp -r dist/* gs://$PROJECT_ID-frontend/
```

---

## 🔒 Security Best Practices

1. **Use Secret Manager** for all sensitive data
2. **Enable VPC** for private database access
3. **IAM roles**: Least privilege principle
4. **Cloud Armor**: DDoS protection
5. **Binary Authorization**: Only deploy signed images
6. **Audit logs**: Enable and monitor
7. **Backup**: Automated daily backups

```bash
# Enable binary authorization
gcloud services enable binaryauthorization.googleapis.com
gcloud container binauthz policy import policy.yaml

# Enable Cloud Armor
gcloud compute security-policies create mindscout-policy \
  --description="DDoS and application protection"
```

---

## 📊 Monitoring Dashboard

**Create custom dashboard**:

```bash
gcloud monitoring dashboards create --config-from-file=dashboard.json
```

**dashboard.json**:
```json
{
  "displayName": "MindScout Monitoring",
  "dashboardFilters": [],
  "mosaicLayout": {
    "columns": 12,
    "tiles": [
      {
        "width": 6,
        "height": 4,
        "widget": {
          "title": "Request Count",
          "xyChart": {
            "dataSets": [{
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"mindscout-backend\"",
                  "aggregation": {
                    "alignmentPeriod": "60s",
                    "perSeriesAligner": "ALIGN_RATE"
                  }
                }
              }
            }]
          }
        }
      }
    ]
  }
}
```

---

## 🚀 Advanced: GKE Deployment

For high-scale production (10K+ concurrent users):

```bash
# Create GKE cluster
gcloud container clusters create mindscout-cluster \
  --region=$REGION \
  --num-nodes=3 \
  --machine-type=e2-medium \
  --enable-autoscaling \
  --min-nodes=3 \
  --max-nodes=10 \
  --enable-autorepair \
  --enable-autoupgrade

# Deploy with Helm
helm install mindscout ./helm-chart
```

See `DEPLOYMENT_GKE.md` for full GKE setup.

---

## 🔄 Migration from Local/Other Cloud

```bash
# Export SQLite data
python scripts/export_data.py > data.json

# Import to Cloud SQL
gcloud sql import sql mindscout-db gs://YOUR-BUCKET/data.sql \
  --database=mindscout
```

---

## 📝 Useful Commands

```bash
# View logs in real-time
gcloud run services logs tail mindscout-backend --region=$REGION

# Update environment variables
gcloud run services update mindscout-backend \
  --set-env-vars="NEW_VAR=value" \
  --region=$REGION

# Scale up/down
gcloud run services update mindscout-backend \
  --max-instances=20 \
  --region=$REGION

# Rollback deployment
gcloud run services update-traffic mindscout-backend \
  --to-revisions=PREVIOUS_REVISION=100 \
  --region=$REGION
```

---

## 🎓 Learning Resources

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Cloud SQL Best Practices](https://cloud.google.com/sql/docs/postgres/best-practices)
- [GCP Free Tier](https://cloud.google.com/free)
- [Architecture Center](https://cloud.google.com/architecture)

---

## Next Steps

1. ✅ Setup GCP project and enable APIs
2. ✅ Create Cloud SQL database
3. ✅ Deploy backend to Cloud Run
4. ✅ Deploy frontend to Cloud Storage
5. ✅ Setup custom domain
6. ✅ Configure monitoring
7. ✅ Setup CI/CD with Cloud Build
