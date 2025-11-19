#!/bin/bash

# MindScout GCP Deployment Script
# This script automates the deployment of MindScout to Google Cloud Platform

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-mindscout-prod}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="mindscout-backend"
DB_INSTANCE="mindscout-db"

echo -e "${GREEN}🚀 MindScout GCP Deployment${NC}"
echo "=================================="
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo ""

# Step 1: Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI not found. Please install it first.${NC}"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker not found. Please install it first.${NC}"
    exit 1
fi

# Step 2: Set active project
echo -e "${YELLOW}Setting active project...${NC}"
gcloud config set project $PROJECT_ID

# Step 3: Enable required APIs
echo -e "${YELLOW}Enabling required GCP APIs...${NC}"
gcloud services enable \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  sqladmin.googleapis.com \
  secretmanager.googleapis.com \
  cloudtasks.googleapis.com \
  storage.googleapis.com \
  compute.googleapis.com \
  --project=$PROJECT_ID

echo -e "${GREEN}✓ APIs enabled${NC}"

# Step 4: Check if secrets exist, create if not
echo -e "${YELLOW}Checking secrets...${NC}"

if ! gcloud secrets describe anthropic-api-key &> /dev/null; then
    echo "Enter your Anthropic API key:"
    read -s ANTHROPIC_KEY
    echo -n "$ANTHROPIC_KEY" | gcloud secrets create anthropic-api-key --data-file=-
    echo -e "${GREEN}✓ Created anthropic-api-key secret${NC}"
else
    echo -e "${GREEN}✓ anthropic-api-key secret exists${NC}"
fi

if ! gcloud secrets describe secret-key &> /dev/null; then
    SECRET_KEY=$(openssl rand -hex 32)
    echo -n "$SECRET_KEY" | gcloud secrets create secret-key --data-file=-
    echo -e "${GREEN}✓ Created secret-key${NC}"
else
    echo -e "${GREEN}✓ secret-key exists${NC}"
fi

# Step 5: Check if Cloud SQL instance exists
echo -e "${YELLOW}Checking Cloud SQL instance...${NC}"

if ! gcloud sql instances describe $DB_INSTANCE &> /dev/null; then
    echo "Creating Cloud SQL instance (this may take 5-10 minutes)..."
    gcloud sql instances create $DB_INSTANCE \
      --database-version=POSTGRES_15 \
      --tier=db-f1-micro \
      --region=$REGION \
      --storage-type=SSD \
      --storage-size=10GB \
      --backup \
      --maintenance-window-day=SUN \
      --maintenance-window-hour=3 \
      --project=$PROJECT_ID

    # Set password
    DB_PASSWORD=$(openssl rand -base64 32)
    gcloud sql users set-password postgres \
      --instance=$DB_INSTANCE \
      --password=$DB_PASSWORD \
      --project=$PROJECT_ID

    # Create database
    gcloud sql databases create mindscout \
      --instance=$DB_INSTANCE \
      --project=$PROJECT_ID

    # Create database URL secret
    INSTANCE_CONNECTION_NAME=$(gcloud sql instances describe $DB_INSTANCE \
      --format='value(connectionName)' \
      --project=$PROJECT_ID)

    DB_URL="postgresql://postgres:${DB_PASSWORD}@/mindscout?host=/cloudsql/${INSTANCE_CONNECTION_NAME}"
    echo -n "$DB_URL" | gcloud secrets create database-url --data-file=-

    echo -e "${GREEN}✓ Cloud SQL instance created${NC}"
else
    echo -e "${GREEN}✓ Cloud SQL instance exists${NC}"
fi

# Step 6: Build and deploy to Cloud Run
echo -e "${YELLOW}Building and deploying to Cloud Run...${NC}"

INSTANCE_CONNECTION_NAME=$(gcloud sql instances describe $DB_INSTANCE \
  --format='value(connectionName)' \
  --project=$PROJECT_ID)

gcloud builds submit \
  --tag gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --project=$PROJECT_ID

gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --set-secrets="ANTHROPIC_API_KEY=anthropic-api-key:latest,DATABASE_URL=database-url:latest,SECRET_KEY=secret-key:latest" \
  --add-cloudsql-instances=$INSTANCE_CONNECTION_NAME \
  --max-instances=10 \
  --min-instances=0 \
  --memory=512Mi \
  --cpu=1 \
  --timeout=300 \
  --concurrency=80 \
  --project=$PROJECT_ID

# Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --format 'value(status.url)' \
  --project=$PROJECT_ID)

echo -e "${GREEN}✓ Backend deployed successfully!${NC}"
echo -e "URL: ${GREEN}$SERVICE_URL${NC}"

# Step 7: Deploy frontend (optional)
read -p "Do you want to deploy the frontend to Cloud Storage? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Building and deploying frontend...${NC}"

    cd frontend

    # Update API URL
    cat > .env.production << EOF
VITE_API_URL=${SERVICE_URL}/api
EOF

    # Build
    npm install
    npm run build

    # Create bucket if it doesn't exist
    BUCKET_NAME="${PROJECT_ID}-frontend"
    if ! gsutil ls -b gs://$BUCKET_NAME &> /dev/null; then
        gsutil mb -l $REGION gs://$BUCKET_NAME
    fi

    # Upload files
    gsutil -m cp -r dist/* gs://$BUCKET_NAME/

    # Make files public
    gsutil -m acl ch -r -u AllUsers:R gs://$BUCKET_NAME/*

    # Set website configuration
    gsutil web set -m index.html -e index.html gs://$BUCKET_NAME

    echo -e "${GREEN}✓ Frontend deployed!${NC}"
    echo -e "URL: ${GREEN}http://storage.googleapis.com/$BUCKET_NAME/index.html${NC}"

    cd ..
fi

# Step 8: Setup Cloud Scheduler (optional)
read -p "Do you want to setup automated daily fetching? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Setting up Cloud Scheduler...${NC}"

    # Check if job exists
    if gcloud scheduler jobs describe fetch-daily-papers --location=$REGION &> /dev/null; then
        echo "Scheduler job already exists, updating..."
        gcloud scheduler jobs update http fetch-daily-papers \
          --location=$REGION \
          --schedule="0 9 * * *" \
          --uri="${SERVICE_URL}/tasks/fetch-papers" \
          --http-method=POST \
          --oidc-service-account-email=${PROJECT_ID}@appspot.gserviceaccount.com \
          --oidc-token-audience="${SERVICE_URL}" \
          --project=$PROJECT_ID
    else
        gcloud scheduler jobs create http fetch-daily-papers \
          --location=$REGION \
          --schedule="0 9 * * *" \
          --uri="${SERVICE_URL}/tasks/fetch-papers" \
          --http-method=POST \
          --oidc-service-account-email=${PROJECT_ID}@appspot.gserviceaccount.com \
          --oidc-token-audience="${SERVICE_URL}" \
          --project=$PROJECT_ID
    fi

    echo -e "${GREEN}✓ Daily fetch scheduled for 9am UTC${NC}"
fi

# Summary
echo ""
echo -e "${GREEN}=================================="
echo "🎉 Deployment Complete!"
echo "==================================${NC}"
echo ""
echo "Backend URL: $SERVICE_URL"
echo "Health Check: ${SERVICE_URL}/health"
echo "API Docs: ${SERVICE_URL}/docs"
echo ""
echo "View logs:"
echo "  gcloud run services logs tail $SERVICE_NAME --region=$REGION"
echo ""
echo "Update deployment:"
echo "  gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Test the API: curl ${SERVICE_URL}/health"
echo "2. Configure custom domain (optional)"
echo "3. Setup monitoring alerts"
echo "4. Configure CORS for your frontend domain"
echo ""
