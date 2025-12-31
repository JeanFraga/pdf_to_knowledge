#!/bin/bash
# setup.sh - Idempotent bootstrap script for Terraform prerequisites
# Run this ONCE before terraform init
# Safe to re-run - all operations are idempotent

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Load PROJECT_ID from .env file
if [[ -f "$PROJECT_ROOT/.env" ]]; then
  export $(grep -E '^GCP_PROJECT_ID=' "$PROJECT_ROOT/.env" | xargs)
  PROJECT_ID="${GCP_PROJECT_ID:-}"
fi

if [[ -z "$PROJECT_ID" ]]; then
  echo "❌ Error: GCP_PROJECT_ID not found in .env file"
  echo "   Create .env from .env.example and set GCP_PROJECT_ID"
  exit 1
fi

REGION="${GCP_REGION:-us-central1}"
TF_STATE_BUCKET="${PROJECT_ID}-tf-state"

echo "🔧 Setting up Terraform prerequisites for project: ${PROJECT_ID}"

# Set project
gcloud config set project "${PROJECT_ID}"

# Enable only the APIs Terraform needs to bootstrap itself
echo "📦 Enabling bootstrap APIs..."
gcloud services enable \
  cloudresourcemanager.googleapis.com \
  serviceusage.googleapis.com \
  storage.googleapis.com \
  iam.googleapis.com

# Create Terraform state bucket (idempotent - gsutil mb fails silently if exists)
echo "🪣 Creating Terraform state bucket..."
if ! gsutil ls -b "gs://${TF_STATE_BUCKET}" &>/dev/null; then
  gsutil mb -p "${PROJECT_ID}" -l "${REGION}" -b on "gs://${TF_STATE_BUCKET}"
  gsutil versioning set on "gs://${TF_STATE_BUCKET}"
  echo "✅ Bucket created: ${TF_STATE_BUCKET}"
else
  echo "✅ Bucket already exists: ${TF_STATE_BUCKET}"
fi

echo ""
echo "✅ Bootstrap complete. You can now run:"
echo "   cd infrastructure/terraform && terraform init"
