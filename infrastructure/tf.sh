#!/bin/bash
# tf.sh - Terraform wrapper with environment support
# Usage:
#   ./tf.sh plan          # dev environment (default)
#   ./tf.sh apply         # dev environment (default)
#   ./tf.sh --prod plan   # prod environment
#   ./tf.sh --prod apply  # prod environment

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TF_DIR="$SCRIPT_DIR/terraform"

# Default to dev
ENV="dev"
TFVARS_FILE="dev.tfvars"

# Check for --prod flag
if [[ "$1" == "--prod" ]]; then
  ENV="prod"
  TFVARS_FILE="prod.tfvars"
  shift  # Remove --prod from arguments
  
  echo "⚠️  WARNING: Production environment selected!"
  echo "   This will create GKE cluster and incur ongoing costs."
  echo ""
fi

# Get terraform command (plan, apply, destroy, etc.)
TF_CMD="${1:-plan}"
shift 2>/dev/null || true  # Remove command from arguments, ignore if none

echo "🔧 Environment: $ENV"
echo "📁 Using: $TFVARS_FILE"
echo ""

cd "$TF_DIR"

# Run terraform with the appropriate tfvars
terraform "$TF_CMD" -var-file="$TFVARS_FILE" "$@"
