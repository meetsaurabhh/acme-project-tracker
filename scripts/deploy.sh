#!/usr/bin/env bash
# Build the frontend and push it to the S3 bucket created by Terraform,
# then invalidate the CloudFront cache so users see the new version.
#
# Prerequisites: AWS CLI configured, terraform apply already run.
set -euo pipefail
cd "$(dirname "$0")/.."

BUCKET="${1:-}"
DISTRIBUTION="${2:-}"

if [[ -z "$BUCKET" || -z "$DISTRIBUTION" ]]; then
  echo "Usage: ./scripts/deploy.sh <s3-bucket-name> <cloudfront-distribution-id>"
  exit 1
fi

echo "==> Building the frontend"
cd frontend && npm ci && npm run build && cd ..

echo "==> Uploading to s3://$BUCKET"
aws s3 sync frontend/dist "s3://$BUCKET" --delete

echo "==> Invalidating CloudFront cache"
aws cloudfront create-invalidation --distribution-id "$DISTRIBUTION" --paths "/*"

echo "Done."
