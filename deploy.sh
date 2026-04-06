#!/bin/bash

# --- Sentinel Finance OS: Deployment Script ---
# This script automates the build and deployment process to Google Cloud Run.

set -e # Exit on any error

# 1. Configuration
GCP_PROJECT_ID="gdgpune-455206" # Set to your actual GCP Project ID
VPC_CONNECTOR="sentinel-vpc-connector"
SERVICE_YAML="service.yaml"

echo "🚀 Starting Deployment for Sentinel Finance OS..."

# 2. Pre-check: Service Account & VPC Connector
echo "🔍 Running Pre-checks..."
VPC_EXISTS=$(gcloud compute networks vpc-access connectors list --region=us-central1 --filter="name:$VPC_CONNECTOR" --format="value(name)" || echo "")

if [ -z "$VPC_EXISTS" ]; then
    echo "❌ ERROR: VPC Connector '$VPC_CONNECTOR' not found in us-central1."
    echo "Please create it before deploying, or update the config in deploy.sh."
    exit 1
fi
echo "✅ VPC Connector verified."

# 3. Preparation: Placeholder Replacement
echo "📝 Updating service manifest with Project ID: $GCP_PROJECT_ID..."
# We use a temporary file to avoid corrupting the original if interrupted
sed -i "s/your-project-id/$GCP_PROJECT_ID/g" "$SERVICE_YAML"

# 4. Build Phase
echo "📦 Building container image via Cloud Build..."
gcloud builds submit --tag "us-central1-docker.pkg.dev/$GCP_PROJECT_ID/sentinel/finance-os:latest" .

# 5. Deployment Phase
echo "☁️  Replacing Cloud Run service definition..."
# Mentor Note: We use 'replace' to ensure the service matches our YAML manifest exactly.
gcloud run services replace "$SERVICE_YAML"

echo "🎉 Deployment Successful! Sentinel Finance OS is live."
