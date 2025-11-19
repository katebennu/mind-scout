# MindScout GCP Quick Start Guide

Get your MindScout app running on Google Cloud Platform in under 30 minutes!

## Prerequisites

- Google Cloud account (free trial available: $300 credit)
- gcloud CLI installed
- Docker installed (for local testing)
- Your Anthropic API key

## Quick Deploy (Automated)

### Option 1: One-Command Deploy

```bash
# Set your project ID
export GCP_PROJECT_ID="mindscout-prod"

# Run the deployment script
./scripts/deploy_gcp.sh
```

That's it! The script will:
- ✅ Create Cloud SQL database
- ✅ Setup secrets
- ✅ Build and deploy backend to Cloud Run
- ✅ Deploy frontend to Cloud Storage
- ✅ Setup daily fetching (optional)

---

## Manual Deploy (Step-by-Step)

### 1. Setup GCP Project (5 minutes)

```bash
# Install gcloud CLI (if not already installed)
# macOS:
brew install google-cloud-sdk

# Login and create project
gcloud auth login
gcloud projects create mindscout-prod --name="MindScout"
gcloud config set project mindscout-prod

# Enable billing (required)
# Go to: https://console.cloud.google.com/billing

# Enable APIs
gcloud services enable \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  sqladmin.googleapis.com \
  secretmanager.googleapis.com
```

### 2. Create Database (10 minutes)

```bash
# Create Cloud SQL instance (takes ~5 min)
gcloud sql instances create mindscout-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1

# Create database
gcloud sql databases create mindscout --instance=mindscout-db

# Set password
DB_PASSWORD=$(openssl rand -base64 32)
gcloud sql users set-password postgres \
  --instance=mindscout-db \
  --password=$DB_PASSWORD

# Store database URL as secret
INSTANCE_NAME=$(gcloud sql instances describe mindscout-db --format='value(connectionName)')
echo -n "postgresql://postgres:${DB_PASSWORD}@/mindscout?host=/cloudsql/${INSTANCE_NAME}" | \
  gcloud secrets create database-url --data-file=-
```

### 3. Store Secrets (2 minutes)

```bash
# Anthropic API key
echo -n "your-anthropic-key-here" | \
  gcloud secrets create anthropic-api-key --data-file=-

# Session secret key
echo -n "$(openssl rand -hex 32)" | \
  gcloud secrets create secret-key --data-file=-
```

### 4. Deploy Backend (5 minutes)

```bash
# Build and deploy
gcloud builds submit --tag gcr.io/mindscout-prod/mindscout-backend

gcloud run deploy mindscout-backend \
  --image gcr.io/mindscout-prod/mindscout-backend \
  --region us-central1 \
  --allow-unauthenticated \
  --set-secrets="ANTHROPIC_API_KEY=anthropic-api-key:latest,DATABASE_URL=database-url:latest" \
  --add-cloudsql-instances=$INSTANCE_NAME \
  --memory=512Mi

# Get the URL
gcloud run services describe mindscout-backend \
  --region us-central1 \
  --format='value(status.url)'
```

### 5. Deploy Frontend (5 minutes)

```bash
cd frontend

# Build
npm install
npm run build

# Create bucket and upload
gsutil mb gs://mindscout-prod-frontend
gsutil -m cp -r dist/* gs://mindscout-prod-frontend/
gsutil -m acl ch -r -u AllUsers:R gs://mindscout-prod-frontend/*
gsutil web set -m index.html -e index.html gs://mindscout-prod-frontend
```

---

## Cost Breakdown

### Free Tier (Always Free)
- Cloud Run: 2M requests/month
- Cloud Build: 120 build-minutes/day
- Secret Manager: 10,000 accesses/month
- Cloud SQL: NOT free

### Expected Monthly Costs (Low Traffic)

| Service | Tier | Cost |
|---------|------|------|
| Cloud SQL | db-f1-micro | $7.67 |
| Cloud Run | < 2M req | $0-5 |
| Cloud Storage | < 5GB | $0.20 |
| **Total** | | **~$10/month** |

### Scaling Costs

**Medium traffic (10K users)**:
- Cloud SQL: $25 (db-g1-small)
- Cloud Run: $20 (auto-scales)
- Total: ~$50/month

**High traffic (100K users)**:
- Cloud SQL: $150 (HA setup)
- Cloud Run: $100
- Redis: $50
- Total: ~$300/month

---

## Testing Your Deployment

```bash
# Get your backend URL
BACKEND_URL=$(gcloud run services describe mindscout-backend \
  --region us-central1 \
  --format='value(status.url)')

# Test health endpoint
curl $BACKEND_URL/health

# Test API docs
open $BACKEND_URL/docs

# Test article listing
curl $BACKEND_URL/api/articles
```

---

## Setup Custom Domain (Optional)

### 1. Add domain to Cloud Run

```bash
gcloud run domain-mappings create \
  --service=mindscout-backend \
  --domain=api.yourdomain.com \
  --region=us-central1
```

### 2. Add DNS records

Cloud Run will show you the DNS records to add. Typically:
```
Type: CNAME
Name: api
Value: ghs.googlehosted.com
```

### 3. Wait for SSL certificate

Google automatically provisions an SSL certificate (takes 15-60 minutes).

---

## Monitoring & Logs

### View Logs

```bash
# Real-time logs
gcloud run services logs tail mindscout-backend --region=us-central1

# Last 100 lines
gcloud logging read "resource.type=cloud_run_revision" --limit=100
```

### Setup Alerts

```bash
# Create uptime check
gcloud monitoring uptime create mindscout-health \
  --resource-type=uptime-url \
  --url="$BACKEND_URL/health"

# View in console
open https://console.cloud.google.com/monitoring
```

---

## Continuous Deployment

### Setup GitHub Integration

1. **Connect Repository**:
```bash
gcloud beta builds triggers create github \
  --repo-name=mindscout \
  --repo-owner=YOUR_GITHUB_USERNAME \
  --branch-pattern=^main$ \
  --build-config=cloudbuild.yaml
```

2. **Push to Deploy**:
```bash
git push origin main
# Automatically builds and deploys!
```

---

## Troubleshooting

### Build Fails

```bash
# Check build logs
gcloud builds list --limit=5
gcloud builds log <BUILD_ID>
```

### Service Won't Start

```bash
# Check Cloud Run logs
gcloud run services logs tail mindscout-backend --region=us-central1

# Common issues:
# - Missing secrets: Check Secret Manager
# - Database connection: Verify Cloud SQL instance name
# - Port: Cloud Run expects port 8080
```

### Database Connection Issues

```bash
# Test Cloud SQL connection
gcloud sql connect mindscout-db --user=postgres

# Check instance status
gcloud sql instances describe mindscout-db
```

### High Costs

```bash
# Check current usage
gcloud billing accounts list

# View detailed billing
open https://console.cloud.google.com/billing

# Reduce costs:
# - Lower Cloud SQL tier
# - Set max instances on Cloud Run
# - Enable Cloud CDN caching
```

---

## Updating Your Deployment

### Backend Update

```bash
# Make changes to code, then:
gcloud builds submit --tag gcr.io/mindscout-prod/mindscout-backend
# Auto-deploys via Cloud Build trigger if setup
```

### Frontend Update

```bash
cd frontend
npm run build
gsutil -m rsync -r -d dist/ gs://mindscout-prod-frontend/
```

### Database Migration

```bash
# Create migration
cd backend
alembic revision --autogenerate -m "Add new table"

# Apply migration (will run on next deployment)
# Or manually:
gcloud run services update mindscout-backend \
  --region=us-central1
```

---

## Scaling Checklist

### Ready for 1K users?
- [x] Cloud Run deployed
- [x] Cloud SQL db-f1-micro
- [x] Secrets in Secret Manager
- [ ] Custom domain
- [ ] Monitoring alerts

### Ready for 10K users?
- [ ] Upgrade Cloud SQL to db-g1-small
- [ ] Add Memorystore Redis
- [ ] Enable Cloud CDN
- [ ] Multi-region deployment
- [ ] Scheduled backups

### Ready for 100K users?
- [ ] Cloud SQL HA (High Availability)
- [ ] Load balancing
- [ ] Cloud Armor (DDoS protection)
- [ ] Cloud Trace (performance monitoring)
- [ ] Database read replicas

---

## Clean Up (Delete Everything)

```bash
# Warning: This deletes everything!

# Delete Cloud Run service
gcloud run services delete mindscout-backend --region=us-central1

# Delete Cloud SQL
gcloud sql instances delete mindscout-db

# Delete secrets
gcloud secrets delete anthropic-api-key
gcloud secrets delete database-url
gcloud secrets delete secret-key

# Delete bucket
gsutil rm -r gs://mindscout-prod-frontend

# Delete project (everything!)
gcloud projects delete mindscout-prod
```

---

## Next Steps

1. ✅ **Configure MCP Server** to connect to cloud API
2. ✅ **Setup scheduled fetching** with Cloud Scheduler
3. ✅ **Add user authentication** (Firebase Auth, OAuth)
4. ✅ **Enable monitoring** (Cloud Monitoring, Sentry)
5. ✅ **Setup backups** (automated SQL backups)
6. ✅ **Add email notifications** (SendGrid, Mailgun)

---

## Getting Help

- **GCP Documentation**: https://cloud.google.com/docs
- **Cloud Run Pricing**: https://cloud.google.com/run/pricing
- **Support**: https://cloud.google.com/support
- **MindScout Issues**: https://github.com/yourusername/mindscout/issues

---

## Cost Optimization Tips

1. **Use Committed Use Discounts**: 37% savings for 1-year commitment
2. **Enable Cloud CDN**: Reduce backend requests
3. **Set max instances**: Prevent runaway costs
4. **Use spot instances**: For non-critical workloads
5. **Delete unused resources**: Regular cleanup
6. **Monitor billing alerts**: Set up budget alerts

```bash
# Set budget alert
gcloud billing budgets create \
  --billing-account=BILLING_ACCOUNT_ID \
  --display-name="MindScout Budget" \
  --budget-amount=50 \
  --threshold-rule=percent=50 \
  --threshold-rule=percent=90 \
  --threshold-rule=percent=100
```

Happy deploying! 🚀
